package com.hagoyama.client;

import com.hagoyama.HagoyamaMod;
import com.mojang.blaze3d.platform.InputConstants;
import net.minecraft.client.KeyMapping;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.RegisterKeyMappingsEvent;
import net.minecraftforge.client.settings.KeyConflictContext;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import org.lwjgl.glfw.GLFW;

@Mod.EventBusSubscriber(modid = HagoyamaMod.MODID, bus = Mod.EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
public final class ClientModEvents {
    public static final KeyMapping SWITCH = new KeyMapping("key.hagoyama.switch_move", KeyConflictContext.IN_GAME,
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_R, "key.categories.hagoyama");
    public static final KeyMapping ZOOM = new KeyMapping("key.hagoyama.zoom", KeyConflictContext.IN_GAME,
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_Z, "key.categories.hagoyama");

    private ClientModEvents() { }

    @SubscribeEvent
    public static void keys(RegisterKeyMappingsEvent e) {
        e.register(SWITCH);
        e.register(ZOOM);
    }
}
