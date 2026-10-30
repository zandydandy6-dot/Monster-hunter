package com.hagoyama;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.living.LivingAttackEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

@Mod.EventBusSubscriber(modid = HagoyamaMod.MODID)
public final class ServerEvents {
    private static final Set<UUID> NIGHT_VISION = new HashSet<>();

    private ServerEvents() { }

    @SubscribeEvent
    public static void onPlayerTick(TickEvent.PlayerTickEvent e) {
        if (e.phase != TickEvent.Phase.END || !(e.player instanceof ServerPlayer p)) return;
        Trance.tick(p);
        clearEye(p);
        if (p.tickCount % 100 == 0) callForSword(p);
    }

    /** Clear Eye (server half): night vision while the awakened sword is held with this move selected. */
    private static void clearEye(ServerPlayer p) {
        ItemStack held = p.getMainHandItem();
        boolean on = p.level().dimension() != Trance.DIM
                && held.getItem() instanceof HagoyamaSwordItem
                && HagoyamaSwordItem.isAwake(held)
                && HagoyamaSwordItem.getMove(held) == Moves.CLEAR_EYE;
        if (on) {
            if (p.tickCount % 20 == 0 || !p.hasEffect(MobEffects.NIGHT_VISION)) {
                p.addEffect(new MobEffectInstance(MobEffects.NIGHT_VISION, 400, 0, false, false, false));
            }
            NIGHT_VISION.add(p.getUUID());
        } else if (NIGHT_VISION.remove(p.getUUID())) {
            p.removeEffect(MobEffects.NIGHT_VISION);
        }
    }

    /** The sword whispers your name when you are near it and have not claimed it yet. */
    private static void callForSword(ServerPlayer p) {
        if (p.level().dimension() == Trance.DIM || Trance.data(p).getBoolean(Trance.K_CLAIMED)) return;
        ServerLevel lv = p.serverLevel();
        boolean near = !lv.getEntitiesOfClass(ItemEntity.class, p.getBoundingBox().inflate(24),
                ie -> ie.getItem().getItem() instanceof HagoyamaSwordItem).isEmpty();
        if (!near) return;
        p.displayClientMessage(Component.literal("\u201C" + p.getName().getString() + "...\u201D")
                .withStyle(ChatFormatting.DARK_AQUA, ChatFormatting.ITALIC), true);
        p.playNotifySound(SoundEvents.SOUL_ESCAPE, SoundSource.AMBIENT, 0.8F, 0.5F);
    }

    @SubscribeEvent
    public static void onPickup(PlayerEvent.ItemPickupEvent e) {
        if (!(e.getEntity() instanceof ServerPlayer p)) return;
        if (!(e.getStack().getItem() instanceof HagoyamaSwordItem)) return;
        var d = Trance.data(p);
        if (d.getBoolean(Trance.K_CLAIMED)) return;
        d.putBoolean(Trance.K_CLAIMED, true);
        Net.sendReflection(p, 200);
        p.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SLOWDOWN, 120, 4, false, false, false));
        p.playNotifySound(SoundEvents.SOUL_ESCAPE, SoundSource.AMBIENT, 1.0F, 0.4F);
        p.sendSystemMessage(Component.literal("You see yourself in the blade. It looks back... then slowly fades.")
                .withStyle(ChatFormatting.GRAY, ChatFormatting.ITALIC));
    }

    /** Nothing can hurt you inside the trance. */
    @SubscribeEvent
    public static void onAttack(LivingAttackEvent e) {
        if (e.getEntity() instanceof Player p && p.level().dimension() == Trance.DIM) e.setCanceled(true);
    }

    @SubscribeEvent
    public static void onLogout(PlayerEvent.PlayerLoggedOutEvent e) {
        if (e.getEntity() instanceof ServerPlayer p) {
            NIGHT_VISION.remove(p.getUUID());
            Trance.onLogout(p);
        }
    }
}
