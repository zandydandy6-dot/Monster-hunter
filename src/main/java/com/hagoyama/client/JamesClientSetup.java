package com.hagoyama.client;

import com.hagoyama.HagoyamaMod;
import com.hagoyama.JamesSetup;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.EntityRenderersEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

@Mod.EventBusSubscriber(modid = HagoyamaMod.MODID, bus = Mod.EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
public final class JamesClientSetup {
    private JamesClientSetup() { }

    @SubscribeEvent
    public static void renderers(EntityRenderersEvent.RegisterRenderers e) {
        e.registerEntityRenderer(JamesSetup.TYPE, JamesRenderer::new);
        e.registerEntityRenderer(JamesSetup.SHADOW, ShadowRenderer::new);
    }
}
