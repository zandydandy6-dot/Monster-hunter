package com.hagoyama;

import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.minecraftforge.common.ForgeSpawnEggItem;
import net.minecraftforge.event.BuildCreativeModeTabContentsEvent;
import net.minecraftforge.event.entity.EntityAttributeCreationEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegisterEvent;

/** Registers James, his spawn egg and the trance shadow figure. */
@Mod.EventBusSubscriber(modid = HagoyamaMod.MODID, bus = Mod.EventBusSubscriber.Bus.MOD)
public final class JamesSetup {
    public static EntityType<James> TYPE;
    public static EntityType<ShadowFigure> SHADOW;
    public static Item EGG;

    private JamesSetup() { }

    @SubscribeEvent
    public static void register(RegisterEvent e) {
        e.register(ForgeRegistries.Keys.ENTITY_TYPES, h -> {
            TYPE = EntityType.Builder.<James>of(James::new, MobCategory.MONSTER)
                    .sized(0.6F, 1.95F).clientTrackingRange(8).build(HagoyamaMod.MODID + ":james");
            h.register(new ResourceLocation(HagoyamaMod.MODID, "james"), TYPE);
            SHADOW = EntityType.Builder.<ShadowFigure>of(ShadowFigure::new, MobCategory.MISC)
                    .sized(0.7F, 2.4F).fireImmune().clientTrackingRange(10).build(HagoyamaMod.MODID + ":shadow_figure");
            h.register(new ResourceLocation(HagoyamaMod.MODID, "shadow_figure"), SHADOW);
        });
        e.register(ForgeRegistries.Keys.ITEMS, h -> {
            EGG = new ForgeSpawnEggItem(() -> TYPE, 0x3FB4F2, 0x2A72A8, new Item.Properties());
            h.register(new ResourceLocation(HagoyamaMod.MODID, "james_spawn_egg"), EGG);
        });
    }

    @SubscribeEvent
    public static void attributes(EntityAttributeCreationEvent e) {
        e.put(TYPE, James.createAttributes().build());
        e.put(SHADOW, ShadowFigure.createAttributes().build());
    }

    @SubscribeEvent
    public static void tabs(BuildCreativeModeTabContentsEvent e) {
        if (e.getTabKey() == CreativeModeTabs.SPAWN_EGGS) e.accept(EGG);
    }
}
