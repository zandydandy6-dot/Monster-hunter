package com.hagoyama;

import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.event.lifecycle.FMLCommonSetupEvent;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

@Mod(HagoyamaMod.MODID)
public class HagoyamaMod {
    public static final String MODID = "hagoyama";

    public static final DeferredRegister<Item> ITEMS = DeferredRegister.create(ForgeRegistries.ITEMS, MODID);
    public static final DeferredRegister<Feature<?>> FEATURES = DeferredRegister.create(ForgeRegistries.FEATURES, MODID);
    public static final DeferredRegister<CreativeModeTab> TABS = DeferredRegister.create(Registries.CREATIVE_MODE_TAB, MODID);

    public static final RegistryObject<Item> HAGOYAMA = ITEMS.register("hagoyama",
            () -> new HagoyamaSwordItem(new Item.Properties().rarity(Rarity.EPIC).fireResistant()));

    public static final RegistryObject<CaveShrineFeature> CAVE_SHRINE = FEATURES.register("cave_shrine",
            () -> new CaveShrineFeature(net.minecraft.world.level.levelgen.feature.configurations.NoneFeatureConfiguration.CODEC));

    public static final RegistryObject<CreativeModeTab> TAB = TABS.register("main",
            () -> CreativeModeTab.builder()
                    .title(Component.translatable("itemGroup.hagoyama"))
                    .icon(() -> new ItemStack(HAGOYAMA.get()))
                    .displayItems((params, out) -> out.accept(HAGOYAMA.get()))
                    .build());

    public HagoyamaMod() {
        IEventBus bus = FMLJavaModLoadingContext.get().getModEventBus();
        ITEMS.register(bus);
        FEATURES.register(bus);
        TABS.register(bus);
        bus.addListener((FMLCommonSetupEvent e) -> e.enqueueWork(Net::register));
    }
}
