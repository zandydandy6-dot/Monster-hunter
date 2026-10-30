package com.hagoyama;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.Tag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BedBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.LeavesBlock;
import net.minecraft.world.level.block.LightBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BedPart;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

/** Everything about the near-death trance: trigger, the "mind" dimension, the figure, and waking up. */
public final class Trance {
    public static final ResourceKey<Level> DIM = ResourceKey.create(Registries.DIMENSION, new ResourceLocation(HagoyamaMod.MODID, "trance"));
    public static final String K_AWAKE = "HagoyamaAwake";
    public static final String K_CLAIMED = "HagoyamaClaimed";
    private static final String K_PREV_MODE = "HagoyamaPrevMode";

    // ---- tuning ----
    public static final int NEAR_DEATH_TICKS = 20 * 60;   // survive 1 minute
    public static final float NEAR_DEATH_HEALTH = 4.0F;   // "less than 2 health bars" = 2 hearts
    private static final double RING = 10.0;              // figure walks a circle this far from you
    private static final double WAKE_DISTANCE = RING - 1.0; // come 1 block closer
    private static final BlockPos ANCHOR = new BlockPos(0, 64, 0);

    private static final String[] LINES = {
            "Open your eyes.",
            "Your heart is slowing. Listen to it.",
            "If you like your life... come closer.",
            "Everything you have built is still here, in the dark.",
            "If you like your life... come closer."
    };

    private static final Map<UUID, Integer> LOW = new HashMap<>();
    private static final Map<UUID, Session> SESSIONS = new HashMap<>();

    private static final class Session {
        UUID figure;
        BlockPos light;
        int age;
        double angle;
    }

    private Trance() { }

    public static CompoundTag data(Player p) {
        CompoundTag root = p.getPersistentData();
        if (!root.contains(Player.PERSISTED_NBT_TAG, Tag.TAG_COMPOUND)) root.put(Player.PERSISTED_NBT_TAG, new CompoundTag());
        return root.getCompound(Player.PERSISTED_NBT_TAG);
    }

    public static boolean isAwake(Player p) { return data(p).getBoolean(K_AWAKE); }

    private static boolean carriesSword(Player p) {
        Inventory inv = p.getInventory();
        for (int i = 0; i < inv.getContainerSize(); i++) {
            if (inv.getItem(i).getItem() instanceof HagoyamaSwordItem) return true;
        }
        return false;
    }

    // ------------------------------------------------------------------ trigger

    public static void tick(ServerPlayer p) {
        if (p.level().dimension() == DIM) { session(p); return; }
        UUID id = p.getUUID();
        if (isAwake(p) || !p.isAlive() || p.isCreative() || p.isSpectator() || !carriesSword(p)) { LOW.remove(id); return; }
        if (p.getHealth() <= NEAR_DEATH_HEALTH) {
            int t = LOW.merge(id, 1, Integer::sum);
            if (t % 40 == 0) p.playNotifySound(SoundEvents.WARDEN_HEARTBEAT, SoundSource.PLAYERS, 0.8F, 0.9F);
            if (t >= NEAR_DEATH_TICKS) { LOW.remove(id); enter(p); }
        } else {
            LOW.remove(id);
        }
    }

    public static void onLogout(ServerPlayer p) {
        LOW.remove(p.getUUID());
        Session s = SESSIONS.remove(p.getUUID());
        if (s != null) cleanup(p.serverLevel(), s);
    }

    // ------------------------------------------------------------------ enter

    public static void enter(ServerPlayer p) {
        ServerLevel mind = p.server.getLevel(DIM);
        if (mind == null) {
            p.sendSystemMessage(Component.literal("The trance dimension is missing (is the mod's data loaded?)."));
            return;
        }
        buildMind(mind);
        data(p).putInt(K_PREV_MODE, p.gameMode.getGameModeForPlayer().getId());
        SESSIONS.put(p.getUUID(), new Session());
        p.removeAllEffects();
        p.setGameMode(GameType.ADVENTURE);
        p.getFoodData().setFoodLevel(20);
        p.fallDistance = 0;
        p.teleportTo(mind, ANCHOR.getX() + 0.5, ANCHOR.getY(), ANCHOR.getZ() + 0.5, 0F, 0F);
        p.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 60, 0, false, false, false));
    }

    // ------------------------------------------------------------------ in the trance

    private static void session(ServerPlayer p) {
        ServerLevel lv = p.serverLevel();
        Session s = SESSIONS.get(p.getUUID());
        if (s == null) { // logged back in inside the trance: send them home
            restoreMode(p);
            returnToBed(p);
            return;
        }
        s.age++;

        if (p.getY() < 40) { p.teleportTo(ANCHOR.getX() + 0.5, ANCHOR.getY(), ANCHOR.getZ() + 0.5); p.fallDistance = 0; }

        Entity fig = s.figure == null ? null : lv.getEntity(s.figure);
        if (fig == null || !fig.isAlive()) { fig = spawnFigure(lv); s.figure = fig.getUUID(); }

        // The figure paces a slow circle, then stops and faces you while it speaks.
        boolean speaking = (s.age % 180) < 55;
        if (!speaking) s.angle += 0.011;
        double ax = ANCHOR.getX() + 0.5, az = ANCHOR.getZ() + 0.5;
        double fx = ax + Math.cos(s.angle) * RING, fz = az + Math.sin(s.angle) * RING;
        float yaw = speaking
                ? (float) Math.toDegrees(Math.atan2(-(p.getX() - fx), p.getZ() - fz))
                : (float) Math.toDegrees(s.angle);
        fig.moveTo(fx, ANCHOR.getY(), fz, yaw, 0F);
        fig.setYHeadRot(yaw);
        if (fig instanceof ShadowFigure sf) sf.setYBodyRot(yaw);

        // The one light in the whole place follows the figure.
        BlockPos lp = BlockPos.containing(fx, ANCHOR.getY() + 1.2, fz);
        if (!lp.equals(s.light)) {
            if (lv.getBlockState(lp).isAir()) lv.setBlock(lp, Blocks.LIGHT.defaultBlockState().setValue(LightBlock.LEVEL, 12), 3);
            if (s.light != null && lv.getBlockState(s.light).is(Blocks.LIGHT)) lv.setBlock(s.light, Blocks.AIR.defaultBlockState(), 3);
            s.light = lp;
        }

        if (s.age % 180 == 40) {
            String line = LINES[(s.age / 180) % LINES.length];
            p.sendSystemMessage(Component.literal("<Hagoyama> ").withStyle(ChatFormatting.DARK_GRAY, ChatFormatting.ITALIC)
                    .append(Component.literal(line).withStyle(ChatFormatting.WHITE)));
            p.playNotifySound(SoundEvents.SOUL_ESCAPE, SoundSource.AMBIENT, 0.7F, 0.5F);
        }
        if (s.age % 40 == 0) p.playNotifySound(SoundEvents.WARDEN_HEARTBEAT, SoundSource.AMBIENT, 0.8F, 0.7F);
        if (s.age % 5 == 0) lv.sendParticles(ParticleTypes.ASH, p.getX(), p.getY() + 1.5, p.getZ(), 6, 5, 3, 5, 0.01);

        if (s.age > 100 && p.distanceTo(fig) <= WAKE_DISTANCE) wake(p, s);
    }

    private static Entity spawnFigure(ServerLevel lv) {
        ShadowFigure f = JamesSetup.SHADOW.create(lv);
        f.setNoAi(true);
        f.setSilent(true);
        f.setInvulnerable(true);
        f.setPersistenceRequired();
        f.moveTo(ANCHOR.getX() + 0.5 + RING, ANCHOR.getY(), ANCHOR.getZ() + 0.5, 90F, 0F);
        lv.addFreshEntity(f);
        return f;
    }

    private static void cleanup(ServerLevel lv, Session s) {
        if (s.figure != null) {
            Entity e = lv.getEntity(s.figure);
            if (e != null) e.discard();
        }
        if (s.light != null && lv.getBlockState(s.light).is(Blocks.LIGHT)) lv.setBlock(s.light, Blocks.AIR.defaultBlockState(), 3);
    }

    // ------------------------------------------------------------------ wake up

    private static void wake(ServerPlayer p, Session s) {
        cleanup(p.serverLevel(), s);
        SESSIONS.remove(p.getUUID());
        data(p).putBoolean(K_AWAKE, true);
        restoreMode(p);
        p.setHealth(p.getMaxHealth());
        p.getFoodData().setFoodLevel(20);
        returnToBed(p);
        p.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 40, 0, false, false, false));
        p.connection.send(new ClientboundSetTitlesAnimationPacket(10, 70, 30));
        p.connection.send(new ClientboundSetSubtitleTextPacket(Component.literal("Hagoyama's eyes are open").withStyle(ChatFormatting.GRAY)));
        p.connection.send(new ClientboundSetTitleTextPacket(Component.literal("Clear Eye").withStyle(ChatFormatting.AQUA)));
    }

    private static void restoreMode(ServerPlayer p) {
        p.setGameMode(GameType.byId(data(p).getInt(K_PREV_MODE)));
    }

    private static void returnToBed(ServerPlayer p) {
        MinecraftServer srv = p.server;
        ServerLevel dest = srv.getLevel(p.getRespawnDimension());
        if (dest == null) dest = srv.overworld();
        Vec3 pos = null;
        BlockPos bed = p.getRespawnPosition();
        if (bed != null) {
            Optional<Vec3> o = Player.findRespawnPositionAndUseSpawnBlock(dest, bed, p.getRespawnAngle(), p.isRespawnForced(), true);
            pos = o.orElse(null);
        }
        if (pos == null) {
            dest = srv.overworld();
            BlockPos sp = dest.getSharedSpawnPos();
            int y = dest.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, sp.getX(), sp.getZ());
            pos = new Vec3(sp.getX() + 0.5, y, sp.getZ() + 0.5);
            p.sendSystemMessage(Component.translatable("block.minecraft.spawn.not_valid"));
        }
        p.fallDistance = 0;
        p.teleportTo(dest, pos.x, pos.y, pos.z, p.getRespawnAngle(), 0F);
    }

    // ------------------------------------------------------------------ the mind

    private static void set(ServerLevel lv, BlockPos pos, BlockState st) {
        lv.setBlock(pos, st, Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE);
    }

    /**
     * Builds the trance place once: a black "eye" floor, hanging neurons (chains), drifting
     * fragments of an ordinary life (bed, workbench, bookshelves, a tree) and glass thought-bubbles.
     * Nothing here gives off light - the only light is the one that follows the figure.
     */
    private static void buildMind(ServerLevel lv) {
        if (lv.getBlockState(new BlockPos(0, 63, 0)).is(Blocks.GILDED_BLACKSTONE)) return;
        RandomSource r = RandomSource.create(1337L);
        BlockState chain = Blocks.CHAIN.defaultBlockState();

        for (int x = -28; x <= 28; x++) {
            for (int z = -28; z <= 28; z++) {
                double d = Math.sqrt(x * x + z * z);
                if (d > 28) continue;
                BlockState top;
                if (d < 1.5) top = Blocks.GILDED_BLACKSTONE.defaultBlockState();          // the pupil
                else if (d < 4) top = Blocks.POLISHED_BLACKSTONE.defaultBlockState();
                else if (d < 6) top = Blocks.BLACK_CONCRETE.defaultBlockState();
                else if (d < 9) top = Blocks.BLACKSTONE.defaultBlockState();
                else top = r.nextFloat() < 0.12F ? Blocks.SCULK.defaultBlockState()       // neural web
                        : (r.nextBoolean() ? Blocks.DEEPSLATE_TILES.defaultBlockState() : Blocks.BLACK_CONCRETE.defaultBlockState());
                set(lv, new BlockPos(x, 63, z), top);
                if (d < 26) set(lv, new BlockPos(x, 62, z), Blocks.DEEPSLATE.defaultBlockState());
                if (d > 5 && r.nextInt(70) == 0) {
                    int len = 4 + r.nextInt(18);
                    for (int i = 0; i < len; i++) set(lv, new BlockPos(x, 61 - i, z), chain);
                }
            }
        }

        // floating memories
        for (int i = 0; i < 46; i++) {
            double ang = r.nextDouble() * Math.PI * 2, dist = 6 + r.nextDouble() * 34;
            int x = (int) (Math.cos(ang) * dist), z = (int) (Math.sin(ang) * dist), y = 68 + r.nextInt(40);
            fragment(lv, r, new BlockPos(x, y, z));
            if (Math.abs(dist - RING) > 2.5) {
                int bottom = dist < 27 ? 64 : y - 3 - r.nextInt(8);
                if (dist >= 27 || r.nextInt(3) == 0) for (int yy = y - 1; yy >= bottom; yy--) set(lv, new BlockPos(x, yy, z), chain);
            }
        }

        // thought-bubbles with a memory inside
        for (int i = 0; i < 10; i++) {
            double ang = r.nextDouble() * Math.PI * 2, dist = 10 + r.nextDouble() * 28;
            BlockPos c = new BlockPos((int) (Math.cos(ang) * dist), 75 + r.nextInt(30), (int) (Math.sin(ang) * dist));
            for (int dx = -3; dx <= 3; dx++) for (int dy = -3; dy <= 3; dy++) for (int dz = -3; dz <= 3; dz++) {
                double d = Math.sqrt(dx * dx + dy * dy + dz * dz);
                if (d <= 3.4 && d >= 2.4) set(lv, c.offset(dx, dy, dz), Blocks.TINTED_GLASS.defaultBlockState());
            }
            fragment(lv, r, c);
        }

        // marker block last, so a half-built mind gets rebuilt
        set(lv, new BlockPos(0, 63, 0), Blocks.GILDED_BLACKSTONE.defaultBlockState());
    }

    private static void fragment(ServerLevel lv, RandomSource r, BlockPos c) {
        BlockState base = switch (r.nextInt(3)) {
            case 0 -> Blocks.GRASS_BLOCK.defaultBlockState();
            case 1 -> Blocks.OAK_PLANKS.defaultBlockState();
            default -> Blocks.MOSSY_COBBLESTONE.defaultBlockState();
        };
        for (int dx = -1; dx <= 1; dx++) for (int dz = -1; dz <= 1; dz++) {
            set(lv, c.offset(dx, 0, dz), base);
            if (Math.abs(dx) + Math.abs(dz) < 2) set(lv, c.offset(dx, -1, dz), Blocks.DIRT.defaultBlockState());
        }
        set(lv, c.below(2), Blocks.DIRT.defaultBlockState());
        BlockPos t = c.above();
        switch (r.nextInt(5)) {
            case 0 -> {
                Direction d = Direction.Plane.HORIZONTAL.getRandomDirection(r);
                set(lv, t, Blocks.RED_BED.defaultBlockState().setValue(BedBlock.FACING, d).setValue(BedBlock.PART, BedPart.FOOT));
                set(lv, t.relative(d), Blocks.RED_BED.defaultBlockState().setValue(BedBlock.FACING, d).setValue(BedBlock.PART, BedPart.HEAD));
            }
            case 1 -> {
                set(lv, t, Blocks.CRAFTING_TABLE.defaultBlockState());
                set(lv, t.east(), Blocks.FURNACE.defaultBlockState());
            }
            case 2 -> {
                set(lv, t, Blocks.BOOKSHELF.defaultBlockState());
                set(lv, t.above(), Blocks.BOOKSHELF.defaultBlockState());
            }
            case 3 -> {
                for (int i = 0; i < 3; i++) set(lv, t.above(i), Blocks.OAK_LOG.defaultBlockState());
                BlockState leaf = Blocks.OAK_LEAVES.defaultBlockState().setValue(LeavesBlock.PERSISTENT, true);
                for (int dx = -1; dx <= 1; dx++) for (int dz = -1; dz <= 1; dz++) set(lv, t.offset(dx, 3, dz), leaf);
            }
            default -> set(lv, t, Blocks.CHEST.defaultBlockState());
        }
    }
}
