package com.hagoyama.client;

import com.hagoyama.HagoyamaMod;
import com.hagoyama.HagoyamaSwordItem;
import com.hagoyama.Moves;
import com.hagoyama.Net;
import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.vertex.BufferBuilder;
import com.mojang.blaze3d.vertex.DefaultVertexFormat;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.Tesselator;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.blaze3d.vertex.VertexFormat;
import com.mojang.math.Axis;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Camera;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.PlayerModel;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.client.gui.Font;
import net.minecraft.client.renderer.GameRenderer;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.InputEvent;
import net.minecraftforge.client.event.RenderLevelStageEvent;
import net.minecraftforge.client.event.ViewportEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import org.joml.Matrix4f;

import java.util.Locale;

@Mod.EventBusSubscriber(modid = HagoyamaMod.MODID, value = Dist.CLIENT)
public final class ClientEvents {
    private static float zoom = 1F;          // current FOV multiplier
    private static float zoomLevel = 4F;     // magnification while the zoom key is held (scroll to change)
    private static long lastNanos = System.nanoTime();

    private static int reflectionTicks, reflectionMax;
    private static Vec3 reflectionPos = Vec3.ZERO;
    private static float reflectionYaw;
    private static PlayerModel<AbstractClientPlayer> wideModel, slimModel;

    private ClientEvents() { }

    /** True while the awakened Hagoyama is held in the main hand with Clear Eye selected. */
    public static boolean clearEyeActive() {
        LocalPlayer p = Minecraft.getInstance().player;
        if (p == null) return false;
        ItemStack s = p.getMainHandItem();
        return s.getItem() instanceof HagoyamaSwordItem && HagoyamaSwordItem.isAwake(s)
                && HagoyamaSwordItem.getMove(s) == Moves.CLEAR_EYE;
    }

    public static void startReflection(int ticks) {
        LocalPlayer p = Minecraft.getInstance().player;
        if (p == null) return;
        double rad = Math.toRadians(p.getYRot());
        reflectionPos = p.position().add(-Math.sin(rad) * 2.4, 0, Math.cos(rad) * 2.4);
        reflectionYaw = p.getYRot() + 180F;
        reflectionTicks = reflectionMax = ticks;
    }

    // ---------------------------------------------------------------- input

    @SubscribeEvent
    public static void clientTick(TickEvent.ClientTickEvent e) {
        if (e.phase != TickEvent.Phase.END) return;
        Minecraft mc = Minecraft.getInstance();
        while (ClientModEvents.SWITCH.consumeClick()) {
            if (mc.player != null && mc.player.getMainHandItem().getItem() instanceof HagoyamaSwordItem) {
                Net.CHANNEL.sendToServer(new Net.SwitchMove());
            }
        }
        if (reflectionTicks > 0) reflectionTicks--;
    }

    @SubscribeEvent
    public static void scroll(InputEvent.MouseScrollingEvent e) {
        if (ClientModEvents.ZOOM.isDown() && clearEyeActive()) {
            zoomLevel = Mth.clamp(zoomLevel + (float) Math.signum(e.getScrollDelta()) * 0.5F, 1.5F, 12F);
            e.setCanceled(true);
        }
    }

    // ---------------------------------------------------------------- zoom

    @SubscribeEvent
    public static void fov(ViewportEvent.ComputeFov e) {
        long now = System.nanoTime();
        float dt = Math.min(0.1F, (now - lastNanos) / 1.0E9F);
        if (e.usedConfiguredFov()) {
            lastNanos = now;
            Minecraft mc = Minecraft.getInstance();
            boolean zooming = mc.player != null && mc.screen == null && ClientModEvents.ZOOM.isDown() && clearEyeActive();
            float target = zooming ? 1F / zoomLevel : 1F;
            zoom += (target - zoom) * (1F - (float) Math.exp(-dt * 12F));
            if (zoom < 0.999F) e.setFOV(e.getFOV() * zoom);
        }
    }

    // ---------------------------------------------------------------- world rendering

    @SubscribeEvent
    public static void renderLevel(RenderLevelStageEvent e) {
        if (e.getStage() != RenderLevelStageEvent.Stage.AFTER_PARTICLES) return;
        Minecraft mc = Minecraft.getInstance();
        if (mc.level == null || mc.player == null) return;
        if (clearEyeActive()) drawHealthBars(e, mc);
        if (reflectionTicks > 0) drawReflection(e, mc);
    }

    private static void drawHealthBars(RenderLevelStageEvent e, Minecraft mc) {
        PoseStack ps = e.getPoseStack();
        Camera cam = e.getCamera();
        Vec3 cp = cam.getPosition();
        float pt = e.getPartialTick();
        MultiBufferSource.BufferSource bs = mc.renderBuffers().bufferSource();

        for (Entity en : mc.level.entitiesForRendering()) {
            if (!(en instanceof LivingEntity le) || le == mc.player || le instanceof ArmorStand || !le.isAlive()) continue;
            double distSq = le.distanceToSqr(mc.player);
            if (distSq > 64 * 64) continue;

            double x = Mth.lerp(pt, le.xo, le.getX()) - cp.x;
            double y = Mth.lerp(pt, le.yo, le.getY()) - cp.y;
            double z = Mth.lerp(pt, le.zo, le.getZ()) - cp.z;
            float k = Math.max(1F, (float) Math.sqrt(distSq) / 10F); // keep far bars readable

            ps.pushPose();
            ps.translate(x, y + le.getBbHeight() + 0.55, z);
            ps.mulPose(cam.rotation());
            ps.scale(-0.025F * k, -0.025F * k, 0.025F * k);
            Matrix4f m = ps.last().pose();

            float frac = Mth.clamp(le.getHealth() / le.getMaxHealth(), 0F, 1F);
            float u = 0.75F;                      // world units per texture pixel
            float fw = 64F * u, fh = 16F * u;     // frame: steel plate with the red eye on its left end
            float fx = -fw / 2F;
            RenderSystem.disableDepthTest();
            RenderSystem.enableBlend();
            RenderSystem.defaultBlendFunc();
            RenderSystem.disableCull();
            RenderSystem.setShader(GameRenderer::getPositionColorTexShader);
            RenderSystem.setShaderTexture(0, BAR_TEXTURE);
            BufferBuilder b = Tesselator.getInstance().getBuilder();
            b.begin(VertexFormat.Mode.QUADS, DefaultVertexFormat.POSITION_COLOR_TEX);
            texQuad(b, m, fx, 0F, fx + fw, fh, 0F, 0F, 64F / BAR_W, 16F / BAR_H, 1F, 1F, 1F, 1F);
            if (frac > 0F) {
                // the gauge sits at x 14..62, y 4..12 of the frame; its fill sprite is 48x8 at (0,16) in the sheet
                float gx = fx + 14F * u, gy = 4F * u, gw = 48F * u, gh = 8F * u;
                texQuad(b, m, gx, gy, gx + gw * frac, gy + gh, 0F, 16F / BAR_H, 48F * frac / BAR_W, 24F / BAR_H,
                        Mth.clamp(2F * (1F - frac), 0F, 1F), Mth.clamp(2F * frac, 0F, 1F), 0.1F, 1F);
            }
            Tesselator.getInstance().end();

            Component label = Component.empty().append(le.getDisplayName()).append(
                    Component.literal(String.format(Locale.ROOT, "  %.1f/%.1f", le.getHealth(), le.getMaxHealth())).withStyle(ChatFormatting.RED));
            mc.font.drawInBatch(label, -mc.font.width(label) / 2F, -10F, 0xFFFFFFFF, false, m, bs, Font.DisplayMode.SEE_THROUGH, 0, LightTexture.FULL_BRIGHT);
            bs.endBatch();
            ps.popPose();
        }
        RenderSystem.enableDepthTest();
        RenderSystem.enableCull();
        RenderSystem.disableBlend();
    }

    private static final ResourceLocation BAR_TEXTURE = new ResourceLocation(HagoyamaMod.MODID, "textures/gui/clear_eye_bar.png");
    private static final float BAR_W = 64F, BAR_H = 32F;

    private static void texQuad(BufferBuilder b, Matrix4f m, float x0, float y0, float x1, float y1,
                                float u0, float v0, float u1, float v1, float r, float g, float bl, float a) {
        b.vertex(m, x0, y0, 0).color(r, g, bl, a).uv(u0, v0).endVertex();
        b.vertex(m, x0, y1, 0).color(r, g, bl, a).uv(u0, v1).endVertex();
        b.vertex(m, x1, y1, 0).color(r, g, bl, a).uv(u1, v1).endVertex();
        b.vertex(m, x1, y0, 0).color(r, g, bl, a).uv(u1, v0).endVertex();
    }

    private static void quad(BufferBuilder b, Matrix4f m, float x0, float y0, float x1, float y1, float r, float g, float bl, float a) {
        b.vertex(m, x0, y0, 0).color(r, g, bl, a).endVertex();
        b.vertex(m, x0, y1, 0).color(r, g, bl, a).endVertex();
        b.vertex(m, x1, y1, 0).color(r, g, bl, a).endVertex();
        b.vertex(m, x1, y0, 0).color(r, g, bl, a).endVertex();
    }

    /** A ghost copy of your own skin, standing in front of you, fading out. */
    private static void drawReflection(RenderLevelStageEvent e, Minecraft mc) {
        AbstractClientPlayer pl = mc.player;
        boolean slim = "slim".equals(pl.getModelName());
        PlayerModel<AbstractClientPlayer> model;
        if (slim) {
            if (slimModel == null) slimModel = new PlayerModel<>(mc.getEntityModels().bakeLayer(ModelLayers.PLAYER_SLIM), true);
            model = slimModel;
        } else {
            if (wideModel == null) wideModel = new PlayerModel<>(mc.getEntityModels().bakeLayer(ModelLayers.PLAYER), false);
            model = wideModel;
        }
        model.young = false;
        model.riding = false;
        model.crouching = false;
        model.setAllVisible(true);

        float life = Mth.clamp((reflectionTicks - e.getPartialTick()) / (float) reflectionMax, 0F, 1F);
        float alpha = 0.8F * life;
        Vec3 cp = e.getCamera().getPosition();
        ResourceLocation skin = pl.getSkinTextureLocation();
        PoseStack ps = e.getPoseStack();

        ps.pushPose();
        ps.translate(reflectionPos.x - cp.x, reflectionPos.y - cp.y + (1F - life) * 0.6, reflectionPos.z - cp.z);
        ps.mulPose(Axis.YP.rotationDegrees(180F - reflectionYaw));
        ps.scale(-1F, -1F, 1F);
        ps.translate(0F, -1.501F, 0F);
        MultiBufferSource.BufferSource bs = mc.renderBuffers().bufferSource();
        RenderType rt = RenderType.entityTranslucent(skin);
        VertexConsumer vc = bs.getBuffer(rt);
        model.renderToBuffer(ps, vc, LightTexture.FULL_BRIGHT, OverlayTexture.NO_OVERLAY, 0.75F, 0.9F, 1F, alpha);
        bs.endBatch(rt);
        ps.popPose();
    }
}
