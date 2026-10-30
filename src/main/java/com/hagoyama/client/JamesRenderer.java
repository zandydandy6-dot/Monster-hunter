package com.hagoyama.client;

import com.hagoyama.HagoyamaMod;
import com.hagoyama.James;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;
import software.bernie.geckolib.model.DefaultedEntityGeoModel;
import software.bernie.geckolib.renderer.GeoEntityRenderer;

/**
 * James. The model keeps the normal blocky Minecraft body (head, body, 2 arms, 2 legs) and adds spiky hair,
 * sweater/pants overlays and the black sword. It is authored at 2x scale for a sharper 128x128 skin, hence 0.5.
 * Files: geo/entity/james.geo.json, animations/entity/james.animation.json, textures/entity/james.png
 */
public class JamesRenderer extends GeoEntityRenderer<James> {
    public JamesRenderer(EntityRendererProvider.Context ctx) {
        super(ctx, new DefaultedEntityGeoModel<>(new ResourceLocation(HagoyamaMod.MODID, "james"), true));
        withScale(0.5F);
        this.shadowRadius = 0.45F;
    }
}
