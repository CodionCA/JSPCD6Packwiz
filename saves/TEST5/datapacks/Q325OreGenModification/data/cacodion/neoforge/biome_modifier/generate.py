import json
import random
import os
from typing import Dict, List, Set

class OreRedistributionGenerator:
    def __init__(self):
        # Define all biome tags (updated with your list)
        self.biome_tags = [
            "#c:is_badlands",
            "#c:is_beach", 
            "#c:is_cave",
            "#c:is_desert",
            "#c:is_forest",
            "#c:is_hill",
            "#c:is_jungle",
            "#c:is_mountain",
            "#c:is_mushroom",
            "#c:is_ocean",
            "#c:is_plains",
            "#c:is_river",
            "#c:is_savanna",
            "#c:is_swamp",
            "#c:is_taiga",
            "#c:is_wasteland"
        ]
        
        # Define all ores in the correct order (lower before upper)
        self.all_ores = [
            "minecraft:ore_andesite_lower",
            "minecraft:ore_andesite_upper",
            "minecraft:ore_coal_lower", 
            "minecraft:ore_coal_upper",
            "minecraft:ore_copper",
            "minecraft:ore_copper_large",
            "minecraft:ore_diamond",
            "minecraft:ore_diamond_buried",
            "minecraft:ore_diamond_large",
            "minecraft:ore_diamond_medium",
            "minecraft:ore_diorite_lower",
            "minecraft:ore_diorite_upper",
            "minecraft:ore_emerald",
            "minecraft:ore_gold",
            "minecraft:ore_gold_deltas",
            "minecraft:ore_gold_extra",
            "minecraft:ore_gold_lower",
            "minecraft:ore_gold_nether",
            "minecraft:ore_granite_lower",
            "minecraft:ore_granite_upper",
            "minecraft:ore_gravel",
            "minecraft:ore_iron_middle",
            "minecraft:ore_iron_small",
            "minecraft:ore_iron_upper",
            "minecraft:ore_lapis",
            "minecraft:ore_lapis_buried",
            "minecraft:ore_redstone",
            "minecraft:ore_redstone_lower",
            "minecraft:ore_tuff",
            "create:zinc_ore",
            "create:striated_ores_overworld"
        ]
        
        # Define additional ores that can be added
        self.additional_ores = [
            "cacodion:ore_gold_large_node",
            "cacodion:ore_calcite",
            "cacodion:ore_coal_extra",
            "cacodion:ore_copper_extra",
            "cacodion:ore_dacite",
            "cacodion:ore_diamond_extra",
            "cacodion:ore_iron_extra",
            "cacodion:ore_lapis_extra",
            "cacodion:ore_ow_nether_gold",
            "cacodion:ore_redstone_extra"
        ]
        
        # Define thematic additions for specific biomes (very sparse)
        self.biome_additions = {
            "#c:is_wasteland": ["cacodion:ore_ow_nether_gold", "cacodion:ore_redstone_extra"],
            "#c:is_badlands": ["cacodion:ore_gold_large_node"],
            "#c:is_cave": ["cacodion:ore_diamond_extra"],
            "#c:is_desert": ["cacodion:ore_gold_large_node"],
            "#c:is_mountain": ["cacodion:ore_iron_extra"],
            "#c:is_jungle": ["cacodion:ore_emerald_extra"],  # Note: not in additional_ores list, will be skipped
            "#c:is_mushroom": ["cacodion:ore_lapis_extra"],
            "#c:is_swamp": ["cacodion:ore_coal_extra"],
            "#c:is_taiga": ["cacodion:ore_copper_extra"],
            "#c:is_forest": ["cacodion:ore_calcite"],
            "#c:is_ocean": ["cacodion:ore_dacite"],
            "#c:is_savanna": ["cacodion:ore_iron_extra"],
            "#c:is_beach": ["cacodion:ore_calcite"],
            "#c:is_hill": ["cacodion:ore_copper_extra"],
            "#c:is_plains": ["cacodion:ore_coal_extra"],
            "#c:is_river": ["cacodion:ore_dacite"]
        }
        
        # Define ore groups that should stay together
        self.ore_groups = {
            "andesite": ["minecraft:ore_andesite_lower", "minecraft:ore_andesite_upper"],
            "coal": ["minecraft:ore_coal_lower", "minecraft:ore_coal_upper"],
            "copper": ["minecraft:ore_copper", "minecraft:ore_copper_large"],
            "diamond": ["minecraft:ore_diamond", "minecraft:ore_diamond_buried", 
                       "minecraft:ore_diamond_large", "minecraft:ore_diamond_medium"],
            "diorite": ["minecraft:ore_diorite_lower", "minecraft:ore_diorite_upper"],
            "gold": ["minecraft:ore_gold", "minecraft:ore_gold_extra", "minecraft:ore_gold_lower"],
            "granite": ["minecraft:ore_granite_lower", "minecraft:ore_granite_upper"],
            "iron": ["minecraft:ore_iron_middle", "minecraft:ore_iron_small", "minecraft:ore_iron_upper"],
            "lapis": ["minecraft:ore_lapis", "minecraft:ore_lapis_buried"],
            "redstone": ["minecraft:ore_redstone", "minecraft:ore_redstone_lower"]
        }
        
        # Define common ores that should be available in multiple tiers
        self.common_ores = {
            "coal": ["minecraft:ore_coal_lower", "minecraft:ore_coal_upper"],
            "iron": ["minecraft:ore_iron_middle", "minecraft:ore_iron_small", "minecraft:ore_iron_upper"],
            "copper": ["minecraft:ore_copper", "minecraft:ore_copper_large"],
            "basic_rocks": ["minecraft:ore_andesite_lower", "minecraft:ore_andesite_upper", 
                           "minecraft:ore_granite_lower", "minecraft:ore_granite_upper",
                           "minecraft:ore_diorite_lower", "minecraft:ore_diorite_upper"]
        }
        
        # Define tier accessibility for common ores
        self.ore_accessibility = {
            # Coal should be available from tier 2 onwards
            "coal": {"min_tier": 2, "ores": ["minecraft:ore_coal_lower", "minecraft:ore_coal_upper"]},
            # Iron should be available from tier 3 onwards  
            "iron": {"min_tier": 3, "ores": ["minecraft:ore_iron_middle", "minecraft:ore_iron_small", "minecraft:ore_iron_upper"]},
            # Copper should be available from tier 4 onwards
            "copper": {"min_tier": 4, "ores": ["minecraft:ore_copper", "minecraft:ore_copper_large"]},
            # Basic rocks should be everywhere
            "rocks": {"min_tier": 8, "ores": ["minecraft:ore_andesite_lower", "minecraft:ore_granite_lower", 
                                             "minecraft:ore_diorite_lower", "minecraft:ore_gravel"]}
        }
        
        # Define biome characteristics for distribution (10 tiers, more generous)
        self.biome_characteristics = {
            # Tier 1: Ultra rare - get the most resources
            "#c:is_mushroom": {"rarity": 1, "difficulty": 5, "ore_multiplier": 1.8, "tier": 1},
            "#c:is_wasteland": {"rarity": 2, "difficulty": 5, "ore_multiplier": 1.7, "tier": 1},
            
            # Tier 2: Very rare - still lots of resources
            "#c:is_badlands": {"rarity": 3, "difficulty": 4, "ore_multiplier": 1.6, "tier": 2},
            "#c:is_cave": {"rarity": 4, "difficulty": 3, "ore_multiplier": 1.5, "tier": 2},
            
            # Tier 3: Rare - good resources
            "#c:is_jungle": {"rarity": 5, "difficulty": 4, "ore_multiplier": 1.4, "tier": 3},
            "#c:is_desert": {"rarity": 6, "difficulty": 4, "ore_multiplier": 1.3, "tier": 3},
            
            # Tier 4: Uncommon - decent resources  
            "#c:is_mountain": {"rarity": 7, "difficulty": 3, "ore_multiplier": 1.2, "tier": 4},
            "#c:is_swamp": {"rarity": 8, "difficulty": 3, "ore_multiplier": 1.1, "tier": 4},
            
            # Tier 5: Moderate - balanced resources
            "#c:is_taiga": {"rarity": 9, "difficulty": 2, "ore_multiplier": 1.0, "tier": 5},
            "#c:is_savanna": {"rarity": 10, "difficulty": 2, "ore_multiplier": 1.0, "tier": 5},
            
            # Tier 6: Common - still reasonable resources
            "#c:is_hill": {"rarity": 11, "difficulty": 2, "ore_multiplier": 0.9, "tier": 6},
            "#c:is_forest": {"rarity": 12, "difficulty": 1, "ore_multiplier": 0.9, "tier": 6},
            
            # Tier 7: Very common - basic resources
            "#c:is_beach": {"rarity": 13, "difficulty": 1, "ore_multiplier": 0.8, "tier": 7},
            "#c:is_river": {"rarity": 14, "difficulty": 1, "ore_multiplier": 0.8, "tier": 7},
            
            # Tier 8: Most common - minimal but still useful
            "#c:is_ocean": {"rarity": 15, "difficulty": 1, "ore_multiplier": 0.7, "tier": 8},
            "#c:is_plains": {"rarity": 16, "difficulty": 1, "ore_multiplier": 0.7, "tier": 8}
        }
        
        # Define realistic biome-specific ore preferences based on real geology
        self.biome_preferences = {
            "#c:is_mountain": {
                "high_priority": ["minecraft:ore_emerald", "minecraft:ore_iron_middle", "minecraft:ore_iron_upper", 
                                "minecraft:ore_coal_lower", "minecraft:ore_coal_upper", "minecraft:ore_copper"],
                "medium_priority": ["minecraft:ore_gold", "minecraft:ore_granite_lower", "minecraft:ore_granite_upper"],
                "low_priority": ["minecraft:ore_diamond"]
            },
            "#c:is_desert": {
                "high_priority": ["minecraft:ore_gold", "minecraft:ore_gold_extra", "minecraft:ore_gold_lower",
                                "minecraft:ore_copper", "minecraft:ore_copper_large"],
                "medium_priority": ["minecraft:ore_iron_middle", "minecraft:ore_redstone"],
                "low_priority": ["minecraft:ore_gravel"]
            },
            "#c:is_badlands": {
                "high_priority": ["minecraft:ore_gold", "minecraft:ore_gold_extra", "minecraft:ore_iron_middle",
                                "minecraft:ore_redstone", "minecraft:ore_redstone_lower"],
                "medium_priority": ["minecraft:ore_copper", "minecraft:ore_coal_lower"],
                "low_priority": ["minecraft:ore_gravel"]
            },
            "#c:is_jungle": {
                "high_priority": ["minecraft:ore_emerald", "minecraft:ore_diamond", "minecraft:ore_diamond_large",
                                "minecraft:ore_gold", "minecraft:ore_iron_middle"],
                "medium_priority": ["minecraft:ore_coal_lower", "minecraft:ore_copper"],
                "low_priority": ["minecraft:ore_lapis"]
            },
            "#c:is_taiga": {
                "high_priority": ["minecraft:ore_coal_lower", "minecraft:ore_coal_upper", "minecraft:ore_iron_middle",
                                "minecraft:ore_copper"],
                "medium_priority": ["minecraft:ore_gold", "minecraft:ore_granite_lower"],
                "low_priority": ["minecraft:ore_gravel"]
            },
            "#c:is_forest": {
                "high_priority": ["minecraft:ore_copper", "minecraft:ore_iron_small", "minecraft:ore_coal_lower"],
                "medium_priority": ["minecraft:ore_andesite_lower"],
                "low_priority": ["minecraft:ore_gravel"]
            },
            "#c:is_swamp": {
                "high_priority": ["minecraft:ore_coal_lower", "minecraft:ore_coal_upper", "minecraft:ore_iron_middle"],
                "medium_priority": ["minecraft:ore_redstone", "minecraft:ore_copper"],
                "low_priority": ["minecraft:ore_gravel"]
            },
            "#c:is_cave": {
                "high_priority": ["minecraft:ore_diamond", "minecraft:ore_diamond_buried", "minecraft:ore_redstone",
                                "minecraft:ore_lapis", "minecraft:ore_iron_middle", "minecraft:ore_gold"],
                "medium_priority": ["minecraft:ore_copper", "minecraft:ore_emerald"],
                "low_priority": ["minecraft:ore_coal_lower"]
            },
            "#c:is_ocean": {
                "high_priority": ["minecraft:ore_gravel", "minecraft:ore_copper"],
                "medium_priority": ["minecraft:ore_lapis"],
                "low_priority": ["minecraft:ore_iron_small"]
            },
            "#c:is_beach": {
                "high_priority": ["minecraft:ore_gravel", "minecraft:ore_copper"],
                "medium_priority": [],
                "low_priority": ["minecraft:ore_iron_small"]
            },
            "#c:is_river": {
                "high_priority": ["minecraft:ore_gravel", "minecraft:ore_copper"],
                "medium_priority": ["minecraft:ore_gold_lower"],
                "low_priority": []
            },
            "#c:is_hill": {
                "high_priority": ["minecraft:ore_copper", "minecraft:ore_iron_middle", "minecraft:ore_coal_lower"],
                "medium_priority": ["minecraft:ore_granite_lower", "minecraft:ore_andesite_lower"],
                "low_priority": ["minecraft:ore_gravel"]
            },
            "#c:is_plains": {
                "high_priority": ["minecraft:ore_iron_small", "minecraft:ore_copper"],
                "medium_priority": ["minecraft:ore_coal_lower"],
                "low_priority": ["minecraft:ore_gravel"]
            },
            "#c:is_savanna": {
                "high_priority": ["minecraft:ore_copper", "minecraft:ore_iron_middle", "minecraft:ore_gold_lower"],
                "medium_priority": ["minecraft:ore_coal_lower", "minecraft:ore_granite_lower"],
                "low_priority": ["minecraft:ore_gravel"]
            },
            "#c:is_mushroom": {
                "high_priority": ["create:zinc_ore", "minecraft:ore_diamond", "minecraft:ore_emerald",
                                "minecraft:ore_gold", "minecraft:ore_redstone", "minecraft:ore_lapis"],
                "medium_priority": ["minecraft:ore_iron_middle", "minecraft:ore_copper"],
                "low_priority": ["minecraft:ore_coal_lower"]
            },
            "#c:is_wasteland": {
                "high_priority": ["minecraft:ore_redstone", "minecraft:ore_redstone_lower", "minecraft:ore_gold",
                                "minecraft:ore_diamond", "minecraft:ore_iron_middle", "create:zinc_ore"],
                "medium_priority": ["minecraft:ore_copper", "minecraft:ore_lapis"],
                "low_priority": ["minecraft:ore_coal_lower"]
            }
        }
        
        # Standard steps for all files
        self.steps = [
            "underground_ores",
            "underground_decoration"
        ]

        self.step = "underground_ores"

    def generate_removal_file(self, biome_tag: str, features_to_remove: List[str]) -> Dict:
        """Generate a removal file for a specific biome"""
        return {
            "type": "neoforge:remove_features",
            "biomes": biome_tag,
            "features": features_to_remove,
            "steps": self.steps
        }

    def generate_addition_file(self, biome_tag: str, features_to_add: List[str]) -> Dict:
        """Generate an addition file for a specific biome"""
        return {
            "type": "neoforge:add_features",
            "biomes": biome_tag,
            "features": features_to_add,
            "step": self.step
        }

    def distribute_ores_realistically(self) -> Dict[str, List[str]]:
        """
        Distribute ores based on real-world geology and biome characteristics
        Ensures every biome gets at least one rock AND one ore, with common ores available across tiers
        """
        distribution = {biome: [] for biome in self.biome_tags}
        assigned_ores = set()
        
        # Calculate more generous base ore counts
        base_ore_count = max(3, len(self.all_ores) // len(self.biome_tags))  # Minimum 3 ores per biome
        
        # First pass: assign high priority ores to biomes
        for biome in self.biome_tags:
            if biome in self.biome_preferences:
                prefs = self.biome_preferences[biome]
                multiplier = self.biome_characteristics[biome]["ore_multiplier"]
                target_count = max(4, int(base_ore_count * multiplier))  # Minimum 4 ores per biome
                
                # Add high priority ores first
                for ore in prefs["high_priority"]:
                    if ore not in assigned_ores and len(distribution[biome]) < target_count:
                        distribution[biome].append(ore)
                        assigned_ores.add(ore)
                        
                        # If this ore is part of a group, try to assign the whole group
                        for group_name, group_ores in self.ore_groups.items():
                            if ore in group_ores:
                                for group_ore in group_ores:
                                    if group_ore not in assigned_ores and len(distribution[biome]) < target_count:
                                        distribution[biome].append(group_ore)
                                        assigned_ores.add(group_ore)
        
        # Second pass: assign medium priority ores
        for biome in self.biome_tags:
            if biome in self.biome_preferences:
                prefs = self.biome_preferences[biome]
                multiplier = self.biome_characteristics[biome]["ore_multiplier"]
                target_count = max(4, int(base_ore_count * multiplier))
                
                for ore in prefs["medium_priority"]:
                    if ore not in assigned_ores and len(distribution[biome]) < target_count:
                        distribution[biome].append(ore)
                        assigned_ores.add(ore)
                        
                        # If this ore is part of a group, try to assign the whole group
                        for group_name, group_ores in self.ore_groups.items():
                            if ore in group_ores:
                                for group_ore in group_ores:
                                    if group_ore not in assigned_ores and len(distribution[biome]) < target_count:
                                        distribution[biome].append(group_ore)
                                        assigned_ores.add(group_ore)
        
        # Third pass: ensure tier-based accessibility for common ores
        for biome in self.biome_tags:
            biome_tier = self.biome_characteristics[biome]["tier"]
            
            # Check each ore type's accessibility
            for ore_type, accessibility in self.ore_accessibility.items():
                if biome_tier <= accessibility["min_tier"]:
                    # This biome should have access to this ore type
                    ore_list = accessibility["ores"]
                    has_ore_type = any(ore in distribution[biome] for ore in ore_list)
                    
                    if not has_ore_type:
                        # Add the first available ore from this type
                        for ore in ore_list:
                            if ore not in assigned_ores:
                                distribution[biome].append(ore)
                                assigned_ores.add(ore)
                                break
                        else:
                            # If all are assigned, duplicate one (common ores can be in multiple biomes)
                            distribution[biome].append(ore_list[0])
        
        # Fourth pass: ensure every biome has at least one rock AND one non-rock ore
        for biome in self.biome_tags:
            rock_ores = ["minecraft:ore_andesite_lower", "minecraft:ore_andesite_upper",
                        "minecraft:ore_diorite_lower", "minecraft:ore_diorite_upper", 
                        "minecraft:ore_granite_lower", "minecraft:ore_granite_upper",
                        "minecraft:ore_gravel", "minecraft:ore_tuff"]
            
            non_rock_ores = [ore for ore in self.all_ores if ore not in rock_ores]
            
            has_rock = any(ore in rock_ores for ore in distribution[biome])
            has_non_rock = any(ore in non_rock_ores for ore in distribution[biome])
            
            # Ensure at least one rock
            if not has_rock:
                for rock in rock_ores:
                    if rock not in assigned_ores:
                        distribution[biome].append(rock)
                        assigned_ores.add(rock)
                        break
                else:
                    # If no unassigned rocks, add gravel (can be duplicated)
                    distribution[biome].append("minecraft:ore_gravel")
            
            # Ensure at least one non-rock ore
            if not has_non_rock:
                # Try to add a basic ore like coal or iron
                basic_ores = ["minecraft:ore_coal_lower", "minecraft:ore_iron_small", "minecraft:ore_copper"]
                for ore in basic_ores:
                    if ore not in assigned_ores:
                        distribution[biome].append(ore)
                        assigned_ores.add(ore)
                        break
                else:
                    # Add copper as fallback (can be duplicated)
                    distribution[biome].append("minecraft:ore_copper")
        
        # Fifth pass: distribute remaining ores to biomes that need more
        remaining_ores = [ore for ore in self.all_ores if ore not in assigned_ores]
        random.shuffle(remaining_ores)
        
        # Sort biomes by ore multiplier (rarest first)
        biomes_by_priority = sorted(self.biome_tags, 
                                   key=lambda b: self.biome_characteristics[b]["ore_multiplier"], 
                                   reverse=True)
        
        for ore in remaining_ores:
            # Find the biome that needs more ores and has space
            for biome in biomes_by_priority:
                multiplier = self.biome_characteristics[biome]["ore_multiplier"]
                target_count = max(4, int(base_ore_count * multiplier))
                
                if len(distribution[biome]) < target_count:
                    distribution[biome].append(ore)
                    break
            else:
                # If no biome needs more, give to the rarest biome
                distribution[biomes_by_priority[0]].append(ore)
        
        # Final pass: ensure minimum counts are met
        for biome in self.biome_tags:
            min_ores = 3  # Absolute minimum
            while len(distribution[biome]) < min_ores:
                # Add common ores that can be duplicated
                common_fallbacks = ["minecraft:ore_copper", "minecraft:ore_gravel", "minecraft:ore_coal_lower"]
                distribution[biome].append(common_fallbacks[len(distribution[biome]) % len(common_fallbacks)])
        
        # Sort ores in each biome to maintain the original order
        for biome in distribution:
            distribution[biome] = [ore for ore in self.all_ores if ore in distribution[biome]]
        
        return distribution

    def generate_all_files(self, output_dir: str = "ore_redistribution"):
        """Generate all redistribution files"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate the distribution
        distribution = self.distribute_ores_realistically()
        
        # Generate removal files for each biome
        for biome_tag in self.biome_tags:
            # Create list of ores to remove (all ores NOT assigned to this biome)
            ores_to_remove = [ore for ore in self.all_ores if ore not in distribution[biome_tag]]
            
            if ores_to_remove:  # Only create file if there are ores to remove
                removal_file = self.generate_removal_file(biome_tag, ores_to_remove)
                
                # Create filename from biome tag
                filename = biome_tag.replace("#c:is_", "").replace("#", "") + "_ore_removal.json"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'w') as f:
                    json.dump(removal_file, f, indent=2)
                
                print(f"Generated: {filename}")
                print(f"  Biome: {biome_tag}")
                print(f"  Keeps: {len(distribution[biome_tag])} ores")
                print(f"  Removes: {len(ores_to_remove)} ores")
                print(f"  Ore list: {', '.join(distribution[biome_tag])}")
                print()
        
        # Generate addition files for biomes with special ores
        for biome_tag in self.biome_tags:
            if biome_tag in self.biome_additions:
                # Filter additions to only include ores that exist in our list
                valid_additions = [ore for ore in self.biome_additions[biome_tag] 
                                 if ore in self.additional_ores]
                
                if valid_additions:
                    addition_file = self.generate_addition_file(biome_tag, valid_additions)
                    
                    # Create filename from biome tag
                    filename = biome_tag.replace("#c:is_", "").replace("#", "") + "_ore_addition.json"
                    filepath = os.path.join(output_dir, filename)
                    
                    with open(filepath, 'w') as f:
                        json.dump(addition_file, f, indent=2)
                    
                    print(f"Generated: {filename}")
                    print(f"  Biome: {biome_tag}")
                    print(f"  Adds: {', '.join(valid_additions)}")
                    print()
        
        # Generate summary file
        self.generate_summary(distribution, output_dir)

    def generate_summary(self, distribution: Dict[str, List[str]], output_dir: str):
        """Generate a summary of the distribution"""
        summary = {
            "distribution_summary": {},
            "ore_locations": {},
            "biome_characteristics": self.biome_characteristics,
            "biome_additions": {}
        }
        
        # Create distribution summary
        for biome, ores in distribution.items():
            additions = []
            if biome in self.biome_additions:
                additions = [ore for ore in self.biome_additions[biome] 
                           if ore in self.additional_ores]
            
            summary["distribution_summary"][biome] = {
                "ore_count": len(ores),
                "ores": ores,
                "additions": additions,
                "ore_multiplier": self.biome_characteristics[biome]["ore_multiplier"],
                "rarity_rank": self.biome_characteristics[biome]["rarity"],
                "tier": self.biome_characteristics[biome]["tier"]
            }
        
        # Create ore location mapping
        for biome, ores in distribution.items():
            for ore in ores:
                if ore not in summary["ore_locations"]:
                    summary["ore_locations"][ore] = []
                summary["ore_locations"][ore].append(biome)
        
        # Add biome additions summary
        for biome, additions in self.biome_additions.items():
            valid_additions = [ore for ore in additions if ore in self.additional_ores]
            if valid_additions:
                summary["biome_additions"][biome] = valid_additions
        
        # Add .disabled extension to prevent game from parsing it
        summary_path = os.path.join(output_dir, "distribution_summary.json.disabled")
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"Generated: distribution_summary.json.disabled")

    def generate_complete_removal_file(self, output_dir: str = "ore_redistribution"):
        """Generate the complete removal file (removes all ores from all biomes)"""
        os.makedirs(output_dir, exist_ok=True)
        
        removal_file = self.generate_removal_file("#c:is_overworld", self.all_ores)
        
        # Add .disabled extension to prevent game from parsing it
        filepath = os.path.join(output_dir, "complete_ore_removal.json.disabled")
        with open(filepath, 'w') as f:
            json.dump(removal_file, f, indent=2)
        
        print(f"Generated: complete_ore_removal.json.disabled (removes all ores from overworld)")

# Example usage
if __name__ == "__main__":
    generator = OreRedistributionGenerator()
    
    print("=== Enhanced Ore Redistribution Generator ===\n")
    
    # Generate redistribution files
    print("Generating biome-specific ore redistribution files with thematic additions...")
    generator.generate_all_files()
    
    print("\n" + "="*50 + "\n")
    
    # Generate complete removal file
    print("Generating complete ore removal file...")
    generator.generate_complete_removal_file()
    
    print("\n=== Generation Complete ===")
    print("Files generated in 'ore_redistribution' directory")
    print("- Individual biome removal files (active .json files)")
    print("- Individual biome addition files (active .json files)")
    print("- distribution_summary.json.disabled (disabled - for reference only)")
    print("- complete_ore_removal.json.disabled (disabled - for reference only)")
    print("\nDistribution Logic:")
    print("- 8 tiers of biomes from ultra-rare to most common")
    print("- Every biome gets minimum 3 ores (at least 1 rock + 1 ore)")
    print("- Common ores available across multiple tiers:")
    print("  * Coal: Available from tier 2+ biomes")
    print("  * Iron: Available from tier 3+ biomes") 
    print("  * Copper: Available from tier 4+ biomes")
    print("  * Rocks: Available everywhere")
    print("- Rarer biomes get more variety, but common ores aren't locked away")
    print("- Mushroom biomes nerfed but still special")
    print("- Sparse thematic additions enhance biome uniqueness:")
    print("  * Wasteland: Nether gold + extra redstone (apocalyptic theme)")
    print("  * Badlands/Desert: Large gold nodes (gold rush theme)")
    print("  * Cave: Extra diamonds (deep mining theme)")
    print("  * Mountain: Extra iron (mountain mining theme)")
    print("  * Mushroom: Extra lapis (magical theme)")
    print("  * Swamp: Extra coal (peat bog theme)")
    print("  * Taiga: Extra copper (northern mining theme)")
    print("  * Forest: Calcite (limestone caves theme)")
    print("  * Ocean/River: Dacite (volcanic ocean floor theme)")
    print("  * And more subtle additions for other biomes...")