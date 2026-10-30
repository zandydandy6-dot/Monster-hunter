package com.hagoyama.client;

import com.hagoyama.HagoyamaMod;
import com.hagoyama.ShadowFigure;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;
import software.bernie.geckolib.model.DefaultedEntityGeoModel;
import software.bernie.geckolib.renderer.GeoEntityRenderer;
import software.bernie.geckolib.renderer.layer.AutoGlowingGeoLayer;

/** The trance shadow: black smoke body, round red eyes that glow in the dark (textures/entity/shadow_figure_glowmask.png). */
public class ShadowRenderer extends GeoEntityRenderer<ShadowFigure> {
    public ShadowRenderer(EntityRendererProvider.Context ctx) {
        super(ctx, new DefaultedEntityGeoModel<>(new ResourceLocation(HagoyamaMod.MODID, "shadow_figure")));
        addRenderLayer(new AutoGlowingGeoLayer<>(this));
        withScale(0.5F);
        this.shadowRadius = 0.4F;
    }
}
