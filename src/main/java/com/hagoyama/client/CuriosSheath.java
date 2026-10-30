package com.hagoyama.client;

import com.hagoyama.HagoyamaMod;
import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.util.function.Supplier;

/**
 * Curios hookup (optional): with Curios installed the Hagoyama sword fits the "back" slot
 * (data/curios/tags/items/back.json) and is drawn sheathed across your back.
 * Curios is reached through reflection on purpose - the mod compiles and runs without it,
 * and a Curios API change can only disable this renderer, never crash the game.
 */
final class CuriosSheath {
    private CuriosSheath() { }

    static void register() {
        try {
            Class<?> rendererType = Class.forName("top.theillusivec4.curios.api.client.ICurioRenderer");
            Class<?> registry = Class.forName("top.theillusivec4.curios.api.client.CuriosRendererRegistry");
            InvocationHandler handler = (proxy, method, args) -> invoke(proxy, method, args);
            Object renderer = Proxy.newProxyInstance(rendererType.getClassLoader(), new Class<?>[]{rendererType}, handler);
            Method register = registry.getMethod("register", Item.class, Supplier.class);
            Supplier<Object> supplier = () -> renderer;
            register.invoke(null, HagoyamaMod.HAGOYAMA.get(), supplier);
        } catch (Throwable t) {
            System.err.println("[hagoyama] Curios sheath renderer not registered: " + t);
        }
    }

    private static Object invoke(Object proxy, Method method, Object[] args) {
        if (method.getDeclaringClass() == Object.class) {
            return switch (method.getName()) {
                case "hashCode" -> System.identityHashCode(proxy);
                case "equals" -> proxy == args[0];
                default -> "HagoyamaSheathRenderer";
            };
        }
        // ICurioRenderer.render(ItemStack, SlotContext, PoseStack, RenderLayerParent, MultiBufferSource, int light, ...)
        if ("render".equals(method.getName()) && args != null && args.length >= 6) {
            draw((ItemStack) args[0], (PoseStack) args[2], (RenderLayerParent<?, ?>) args[3],
                    (MultiBufferSource) args[4], (Integer) args[5]);
        }
        return null;
    }

    private static void draw(ItemStack stack, PoseStack ps, RenderLayerParent<?, ?> parent, MultiBufferSource buffers, int light) {
        if (!(parent.getModel() instanceof HumanoidModel<?> model)) return;
        Minecraft mc = Minecraft.getInstance();
        ps.pushPose();
        model.body.translateAndRotate(ps);          // follow the torso (sneaking tilts it too)
        ps.translate(0.0F, 0.34F, 0.2F);            // middle of the back, just behind the chest
        ps.scale(0.9F, 0.9F, 0.9F);                 // hilt over the right shoulder, tip toward the left hip
        mc.getItemRenderer().renderStatic(stack, ItemDisplayContext.NONE, light, OverlayTexture.NO_OVERLAY, ps, buffers, mc.level, 0);
        ps.popPose();
    }
}
