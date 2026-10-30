package com.hagoyama;

import com.mojang.serialization.Codec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.PointedDripstoneBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.FeaturePlaceContext;
import net.minecraft.world.level.levelgen.feature.configurations.NoneFeatureConfiguration;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * A rare underground cave system: 5-7 irregular cave chambers joined by winding tunnels (no doors),
 * dripstone, moss and tuff. The last chamber holds a single stone block with Hagoyama floating above it.
 */
public class CaveShrineFeature extends Feature<NoneFeatureConfiguration> {
    public CaveShrineFeature(Codec<NoneFeatureConfiguration> codec) { super(codec); }

    @Override
    public boolean place(FeaturePlaceContext<NoneFeatureConfiguration> ctx) {
        BlockPos o = ctx.origin();
        // One shrine per region, at a spot that only depends on the world seed - /hagoyama locate computes the same spot.
        ShrineLocator.Site site = ShrineLocator.siteInChunk(ctx.level().getSeed(), o.getX() >> 4, o.getZ() >> 4);
        if (site == null) return false;
        Shrine s = new Shrine(ctx.level(), ctx.random(), site.chunkX() << 4, site.chunkZ() << 4);
        return s.build(site.y());
    }

    /** Per-call state (features run on several threads, so nothing is stored on the Feature itself). */
    private static final class Shrine {
        final WorldGenLevel level;
        final RandomSource rnd;
        final int cx, cz;
        final Set<Long> carved = new HashSet<>();

        Shrine(WorldGenLevel level, RandomSource rnd, int cx, int cz) {
            this.level = level; this.rnd = rnd; this.cx = cx; this.cz = cz;
        }

        // Only touch blocks inside the area a feature is allowed to read and write.
        boolean ok(int x, int y, int z) {
            return x >= cx - 12 && x <= cx + 27 && z >= cz - 12 && z <= cz + 27
                    && y > level.getMinBuildHeight() + 6 && y < level.getMaxBuildHeight() - 6;
        }
        BlockState at(int x, int y, int z) {
            return ok(x, y, z) ? level.getBlockState(new BlockPos(x, y, z)) : Blocks.STONE.defaultBlockState();
        }
        boolean solid(int x, int y, int z) {
            BlockState s = at(x, y, z);
            return !s.isAir() && s.getFluidState().isEmpty();
        }
        void put(int x, int y, int z, BlockState s) {
            if (ok(x, y, z)) level.setBlock(new BlockPos(x, y, z), s, 2);
        }

        void carve(int x, int y, int z) {
            if (!ok(x, y, z)) return;
            BlockState st = level.getBlockState(new BlockPos(x, y, z));
            if (!st.getFluidState().isEmpty() || st.is(Blocks.BEDROCK)) return;
            level.setBlock(new BlockPos(x, y, z), Blocks.CAVE_AIR.defaultBlockState(), 2);
            carved.add(BlockPos.asLong(x, y, z));
        }

        void ellipsoid(double x, double y, double z, double rx, double ry, double rz) {
            for (int ix = (int) Math.floor(x - rx); ix <= Math.ceil(x + rx); ix++)
                for (int iy = (int) Math.floor(y - ry); iy <= Math.ceil(y + ry); iy++)
                    for (int iz = (int) Math.floor(z - rz); iz <= Math.ceil(z + rz); iz++) {
                        double dx = (ix + 0.5 - x) / rx, dy = (iy + 0.5 - y) / ry, dz = (iz + 0.5 - z) / rz;
                        double wobble = 0.18 * Math.sin(ix * 0.7 + iz * 0.5) * Math.sin(iy * 0.9 + ix * 0.3);
                        if (dx * dx + dy * dy + dz * dz + wobble <= 1.0) carve(ix, iy, iz);
                    }
        }

        void blob(Vec3 c, double scale) {
            int n = 3 + rnd.nextInt(3);
            for (int k = 0; k < n; k++) {
                ellipsoid(c.x + (rnd.nextDouble() - 0.5) * 5, c.y + (rnd.nextDouble() - 0.5) * 2.5, c.z + (rnd.nextDouble() - 0.5) * 5,
                        (3 + rnd.nextDouble() * 2) * scale, (2 + rnd.nextDouble() * 1.6) * scale, (3 + rnd.nextDouble() * 2) * scale);
            }
        }

        void tunnel(Vec3 a, Vec3 b, double radius) {
            double dx = b.x - a.x, dy = b.y - a.y, dz = b.z - a.z;
            int steps = (int) (Math.sqrt(dx * dx + dy * dy + dz * dz) * 2.5) + 1;
            double ph = rnd.nextDouble() * 6.28;
            for (int i = 0; i <= steps; i++) {
                double t = i / (double) steps;
                double r = radius + 0.4 * Math.sin(t * 9 + ph);
                ellipsoid(a.x + dx * t + Math.sin(t * 7 + ph) * 1.4, a.y + dy * t + Math.sin(t * 5 + ph * 2) * 0.8,
                        a.z + dz * t + Math.cos(t * 6 + ph) * 1.4, r, r * 0.85, r);
            }
        }

        boolean build(int originY) {
            List<Vec3> rooms = new ArrayList<>();
            Vec3 cur = new Vec3(cx + 8.5, originY, cz + 8.5);
            rooms.add(cur);
            int target = 5 + rnd.nextInt(3);
            for (int guard = 0; rooms.size() < target && guard < 60; guard++) {
                double ang = rnd.nextDouble() * Math.PI * 2, dist = 8 + rnd.nextDouble() * 4;
                Vec3 nxt = cur.add(Math.cos(ang) * dist, rnd.nextInt(5) - 2, Math.sin(ang) * dist);
                if (Math.abs(nxt.x - (cx + 8)) > 15 || Math.abs(nxt.z - (cz + 8)) > 15) continue;
                boolean tooClose = false;
                for (Vec3 r : rooms) if (Math.hypot(r.x - nxt.x, r.z - nxt.z) < 6) tooClose = true;
                if (tooClose) continue;
                tunnel(cur, nxt, 1.5);
                rooms.add(nxt);
                cur = nxt;
            }
            if (rooms.size() < 3) return false;
            tunnel(rooms.get(0), rooms.get(2), 1.3); // a loop, like real cave networks

            // a way in: a long rising tunnel from the first chamber
            double ea = rnd.nextDouble() * Math.PI * 2;
            Vec3 first = rooms.get(0);
            tunnel(first, first.add(Math.cos(ea) * 14, 6, Math.sin(ea) * 14), 1.6);

            for (int i = 0; i < rooms.size(); i++) blob(rooms.get(i), i == rooms.size() - 1 ? 1.35 : 0.9 + rnd.nextDouble() * 0.5);

            Vec3 last = rooms.get(rooms.size() - 1);
            int px = (int) Math.floor(last.x), pz = (int) Math.floor(last.z);
            ellipsoid(px + 0.5, last.y, pz + 0.5, 3.5, 3.2, 3.5);

            decorate();

            // pedestal: first air block above solid ground, searching down from the chamber centre
            int py = (int) Math.floor(last.y);
            while (py > last.y - 8 && !solid(px, py - 1, pz)) py--;
            ellipsoid(px + 0.5, py + 2, pz + 0.5, 2.4, 3, 2.4);
            put(px, py, pz, Blocks.STONE.defaultBlockState());

            ItemEntity sword = new ItemEntity(level.getLevel(), px + 0.5, py + 1.6, pz + 0.5, new ItemStack(HagoyamaMod.HAGOYAMA.get()));
            sword.setNoGravity(true);
            sword.setDeltaMovement(Vec3.ZERO);
            sword.setUnlimitedLifetime();
            sword.setInvulnerable(true);
            level.addFreshEntity(sword);
            return true;
        }

        void decorate() {
            BlockState tipUp = Blocks.POINTED_DRIPSTONE.defaultBlockState().setValue(PointedDripstoneBlock.TIP_DIRECTION, Direction.UP);
            BlockState tipDown = Blocks.POINTED_DRIPSTONE.defaultBlockState().setValue(PointedDripstoneBlock.TIP_DIRECTION, Direction.DOWN);
            for (long l : new ArrayList<>(carved)) {
                BlockPos p = BlockPos.of(l);
                int x = p.getX(), y = p.getY(), z = p.getZ();
                boolean floor = !carved.contains(BlockPos.asLong(x, y - 1, z)) && solid(x, y - 1, z);
                boolean ceil = !carved.contains(BlockPos.asLong(x, y + 1, z)) && solid(x, y + 1, z);
                float f = rnd.nextFloat();
                if (floor) {
                    if (f < 0.07F) put(x, y, z, tipUp);
                    else if (f < 0.12F) { put(x, y - 1, z, Blocks.MOSS_BLOCK.defaultBlockState()); if (rnd.nextBoolean()) put(x, y, z, Blocks.MOSS_CARPET.defaultBlockState()); }
                    else if (f < 0.16F) put(x, y - 1, z, Blocks.DRIPSTONE_BLOCK.defaultBlockState());
                }
                f = rnd.nextFloat();
                if (ceil) {
                    if (f < 0.09F) put(x, y, z, tipDown);
                    else if (f < 0.13F) put(x, y + 1, z, Blocks.DRIPSTONE_BLOCK.defaultBlockState());
                }
                // wall variety
                for (Direction d : Direction.Plane.HORIZONTAL) {
                    int wx = x + d.getStepX(), wz = z + d.getStepZ();
                    if (carved.contains(BlockPos.asLong(wx, y, wz)) || !solid(wx, y, wz)) continue;
                    float w = rnd.nextFloat();
                    if (w < 0.05F) put(wx, y, wz, Blocks.TUFF.defaultBlockState());
                    else if (w < 0.07F) put(wx, y, wz, Blocks.CALCITE.defaultBlockState());
                }
            }
        }
    }
}
