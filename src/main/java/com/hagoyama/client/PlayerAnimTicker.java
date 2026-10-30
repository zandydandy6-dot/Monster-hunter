package com.hagoyama.client;

import com.hagoyama.HagoyamaMod;
import com.hagoyama.HagoyamaSwordItem;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Starts a slash animation the moment a player swings the Hagoyama sword. A swing is visible on every client
 * (the server tells everyone), so other players see your combo without any extra networking.
 * Hit again within a second to chain slash 1 -> 2 -> 3.
 */
@Mod.EventBusSubscriber(modid = HagoyamaMod.MODID, value = Dist.CLIENT)
public final class PlayerAnimTicker {
    private static final Map<UUID, Integer> COMBO = new HashMap<>();
    private static final Map<UUID, Long> LAST = new HashMap<>();

    private PlayerAnimTicker() { }

    @SubscribeEvent
    public static void tick(TickEvent.ClientTickEvent e) {
        if (e.phase != TickEvent.Phase.END) return;
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null) {
            COMBO.clear();
            LAST.clear();
            return;
        }
        long now = mc.level.getGameTime();
        for (AbstractClientPlayer p : mc.level.players()) {
            // swingTime == 0 happens for exactly one tick at the start of every swing
            if (p.swinging && p.swingTime == 0 && p.getMainHandItem().getItem() instanceof HagoyamaSwordItem) {
                UUID id = p.getUUID();
                int n = COMBO.getOrDefault(id, 0);
                if (now - LAST.getOrDefault(id, -100L) > 20L) n = 0; // combo resets after a pause
                PlayerAnims.play(p, "hagoyama_slash_" + (n % 3 + 1));
                COMBO.put(id, n + 1);
                LAST.put(id, now);
            }
        }
    }
}
