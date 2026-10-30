package com.hagoyama.client;

import com.hagoyama.HagoyamaMod;
import dev.kosmx.playerAnim.api.layered.IAnimation;
import dev.kosmx.playerAnim.api.layered.KeyframeAnimationPlayer;
import dev.kosmx.playerAnim.api.layered.ModifierLayer;
import dev.kosmx.playerAnim.minecraftApi.PlayerAnimationAccess;
import dev.kosmx.playerAnim.minecraftApi.PlayerAnimationFactory;
import dev.kosmx.playerAnim.minecraftApi.PlayerAnimationRegistry;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.resources.ResourceLocation;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.ModList;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.event.lifecycle.FMLClientSetupEvent;

/**
 * Player Animation Library hookup: the three sword slashes in assets/hagoyama/player_animation/ are played on
 * any player (yours and other people's) who swings the Hagoyama sword. See PlayerAnimTicker for the trigger.
 */
@Mod.EventBusSubscriber(modid = HagoyamaMod.MODID, bus = Mod.EventBusSubscriber.Bus.MOD, value = Dist.CLIENT)
public final class PlayerAnims {
    public static final ResourceLocation LAYER = new ResourceLocation(HagoyamaMod.MODID, "sword_combo");

    private PlayerAnims() { }

    @SubscribeEvent
    public static void init(FMLClientSetupEvent e) {
        PlayerAnimationFactory.ANIMATION_DATA_FACTORY.registerFactory(LAYER, 1000, player -> new ModifierLayer<>());
        if (ModList.get().isLoaded("curios")) {
            CuriosSheath.register(); // optional: carry the sword sheathed on your back
        }
    }

    @SuppressWarnings("unchecked")
    public static void play(AbstractClientPlayer player, String name) {
        var layer = (ModifierLayer<IAnimation>) PlayerAnimationAccess.getPlayerAssociatedData(player).get(LAYER);
        var animation = PlayerAnimationRegistry.getAnimation(new ResourceLocation(HagoyamaMod.MODID, name));
        if (layer != null && animation != null) {
            layer.setAnimation(new KeyframeAnimationPlayer(animation));
        }
    }
}
