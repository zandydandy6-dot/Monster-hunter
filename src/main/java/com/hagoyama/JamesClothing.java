package com.hagoyama;

import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.item.ArmorItem;
import net.minecraft.world.item.ArmorMaterial;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraftforge.event.BuildCreativeModeTabContentsEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegisterEvent;

/**
 * James's clothes: a sweater, trousers and boots that you can wear. Killing James drops exactly one of them
 * (see data/hagoyama/loot_tables/entities/james.json).
 */
@Mod.EventBusSubscriber(modid = HagoyamaMod.MODID, bus = Mod.EventBusSubscriber.Bus.MOD)
public final class JamesClothing {
    public static Item SWEATER;
    public static Item TROUSERS;
    public static Item BOOTS;

    private JamesClothing() { }

    /** Cloth: roughly leather strength, but they look far better. */
    public enum Material implements ArmorMaterial {
        JAMES;

        @Override public int getDurabilityForType(ArmorItem.Type type) {
            int base = switch (type) {
                case BOOTS -> 13;
                case LEGGINGS -> 15;
                case CHESTPLATE -> 16;
                case HELMET -> 11;
            };
            return base * 8;
        }
        @Override public int getDefenseForType(ArmorItem.Type type) {
            return switch (type) {
                case BOOTS -> 1;
                case LEGGINGS -> 2;
                case CHESTPLATE -> 3;
                case HELMET -> 1;
            };
        }
        @Override public int getEnchantmentValue() { return 15; }
        @Override public SoundEvent getEquipSound() { return SoundEvents.ARMOR_EQUIP_LEATHER; }
        @Override public Ingredient getRepairIngredient() { return Ingredient.of(Items.BLUE_WOOL); }
        /** "hagoyama:james" -> textures/models/armor/james_layer_1.png and james_layer_2.png */
        @Override public String getName() { return HagoyamaMod.MODID + ":james"; }
        @Override public float getToughness() { return 0.0F; }
        @Override public float getKnockbackResistance() { return 0.0F; }
    }

    @SubscribeEvent
    public static void register(RegisterEvent e) {
        e.register(ForgeRegistries.Keys.ITEMS, h -> {
            SWEATER = new ArmorItem(Material.JAMES, ArmorItem.Type.CHESTPLATE, new Item.Properties());
            TROUSERS = new ArmorItem(Material.JAMES, ArmorItem.Type.LEGGINGS, new Item.Properties());
            BOOTS = new ArmorItem(Material.JAMES, ArmorItem.Type.BOOTS, new Item.Properties());
            h.register(new ResourceLocation(HagoyamaMod.MODID, "james_sweater"), SWEATER);
            h.register(new ResourceLocation(HagoyamaMod.MODID, "james_trousers"), TROUSERS);
            h.register(new ResourceLocation(HagoyamaMod.MODID, "james_boots"), BOOTS);
        });
    }

    @SubscribeEvent
    public static void tabs(BuildCreativeModeTabContentsEvent e) {
        if (e.getTabKey() == CreativeModeTabs.COMBAT || e.getTabKey().equals(HagoyamaMod.TAB.getKey())) {
            e.accept(SWEATER);
            e.accept(TROUSERS);
            e.accept(BOOTS);
        }
    }
}
