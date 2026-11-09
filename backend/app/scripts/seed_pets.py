"""
Seed script generating 35+ realistic pet records with rich qualitative profiles and 768-dim embeddings.
[FROM MARKDOWN] Step 1.3: Ingestion & Seed Data.
"""

import sys
import os
import json
import logging
from typing import List, Dict, Any

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.database.connection import get_sync_db
from app.database.indexes import setup_standard_indexes, setup_atlas_vector_search_index
from app.services.embedding import generate_embedding
from app.models.pet import Pet

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_pets")


RAW_PET_RECORDS: List[Dict[str, Any]] = [
    {
        "_id": "pet_dog_001",
        "name": "Buddy",
        "species": "dog",
        "breed": "Golden Retriever",
        "age_months": 24,
        "gender": "Male",
        "size": "medium",
        "energy_level": 4,
        "good_with_kids": True,
        "good_with_other_pets": True,
        "temperament": ["Active", "Family Friendly", "Good with Kids", "Loyal"],
        "housing_requirement": "apartment_or_house",
        "bio_text": "A playful and affectionate boy who loves walks, belly rubs, and being around people! Always ready for fetch in the park and adores children.",
        "quirks": ["Carries a favorite tennis ball everywhere", "Greets you with happy tippy-taps"],
        "exercise_needs": "60+ minutes daily walks and active play",
        "triggers": ["Loud thunder storms", "Sudden loud vacuums"],
        "photo_url": "https://images.unsplash.com/photo-1552053831-71594a27632d"
    },
    {
        "_id": "pet_dog_002",
        "name": "Luna",
        "species": "dog",
        "breed": "Siberian Husky",
        "age_months": 18,
        "gender": "Female",
        "size": "large",
        "energy_level": 5,
        "good_with_kids": True,
        "good_with_other_pets": False,
        "temperament": ["Adventurous", "Vocal", "High Energy", "Playful"],
        "housing_requirement": "house_with_yard",
        "bio_text": "An energetic, striking girl who loves mountain trails and outdoor endurance running. Very talkative with signature husky 'awoo' singing.",
        "quirks": ["Dramatic vocal commentary before breakfast", "Loves sleeping belly-up in cool corners"],
        "exercise_needs": "90+ minutes intense jogging or hiking daily",
        "triggers": ["Small prey animals (cats, squirrels)"],
        "photo_url": "https://images.unsplash.com/photo-1537151625747-768eb6cf92b2"
    },
    {
        "_id": "pet_dog_003",
        "name": "Milo",
        "species": "dog",
        "breed": "French Bulldog",
        "age_months": 36,
        "gender": "Male",
        "size": "small",
        "energy_level": 2,
        "good_with_kids": True,
        "good_with_other_pets": True,
        "temperament": ["Chill", "Affectionate", "Couch Potato", "Adaptable"],
        "housing_requirement": "apartment",
        "bio_text": "A calm, comical snuggle bug perfectly tailored for cozy apartment living. Prefers short strolls followed by a generous afternoon nap on the sofa.",
        "quirks": ["Snores peacefully during movie nights", "Tilts his head at every doorbell sound"],
        "exercise_needs": "20-30 minutes casual strolls in moderate temperatures",
        "triggers": ["Excessive summer heat", "Strenuous uphill stairs"],
        "photo_url": "https://images.unsplash.com/photo-1583511655857-d19b40a7a54e"
    },
    {
        "_id": "pet_dog_004",
        "name": "Bella",
        "species": "dog",
        "breed": "Border Collie",
        "age_months": 30,
        "gender": "Female",
        "size": "medium",
        "energy_level": 5,
        "good_with_kids": True,
        "good_with_other_pets": True,
        "temperament": ["Intelligent", "Attentive", "Active", "Agile"],
        "housing_requirement": "house_with_yard",
        "bio_text": "Whip-smart working breed that thrives on mental challenges, frisbee agility, and structured obedience games. Needs an engaged handler.",
        "quirks": ["Rounds up her toys into neat piles", "Stares intently waiting for task cues"],
        "exercise_needs": "75+ minutes vigorous exercise plus interactive brain games",
        "triggers": ["Boredom when left isolated for long hours"],
        "photo_url": "https://images.unsplash.com/photo-1517423440428-a5a00ad493e8"
    },
    {
        "_id": "pet_dog_005",
        "name": "Rocky",
        "species": "dog",
        "breed": "Boxer Mix",
        "age_months": 42,
        "gender": "Male",
        "size": "large",
        "energy_level": 4,
        "good_with_kids": True,
        "good_with_other_pets": False,
        "temperament": ["Goofy", "Loving", "Protective", "Playful"],
        "housing_requirement": "apartment_or_house",
        "bio_text": "A muscular softie with a heart of gold. Loves playing tug-of-war and offering warm whole-body hugs to his human family members.",
        "quirks": ["Wiggles his entire back half when excited", "Does playful front-paw boxing dances"],
        "exercise_needs": "60 minutes brisk daily walks and backyard fetch",
        "triggers": ["Unfamiliar large male dogs approaching too fast"],
        "photo_url": "https://images.unsplash.com/photo-1543466835-00a7907e9de1"
    },
    {
        "_id": "pet_dog_006",
        "name": "Daisy",
        "species": "dog",
        "breed": "Cavalier King Charles Spaniel",
        "age_months": 28,
        "gender": "Female",
        "size": "small",
        "energy_level": 2,
        "good_with_kids": True,
        "good_with_other_pets": True,
        "temperament": ["Gentle", "Sweet", "Companion", "Quiet"],
        "housing_requirement": "apartment",
        "bio_text": "The ultimate lap dog with soulful eyes and silky ears. Excellent for quiet working-from-home guardians or gentle seniors desiring companionship.",
        "quirks": ["Rests her chin right over your knee when reading", "Loves warm sunbeams across carpet"],
        "exercise_needs": "30 minutes leisurely scenic park walks",
        "triggers": ["Harsh yelling or sudden loud clatter"],
        "photo_url": "https://images.unsplash.com/photo-1583337130417-3346a1be7dee"
    },
    {
        "_id": "pet_dog_007",
        "name": "Zeus",
        "species": "dog",
        "breed": "German Shepherd",
        "age_months": 48,
        "gender": "Male",
        "size": "large",
        "energy_level": 4,
        "good_with_kids": False,
        "good_with_other_pets": True,
        "temperament": ["Protective", "Disciplined", "Devoted", "Observant"],
        "housing_requirement": "house_with_yard",
        "bio_text": "Noble guardian with exceptional training foundations. Very devoted to his primary handler, best suited for experienced adult households.",
        "quirks": ["Performs routine perimeter checks around the yard", "Loves scent-tracking games"],
        "exercise_needs": "60-80 minutes structured walks and agility tasks",
        "triggers": ["Sudden unpredictable toddler movements"],
        "photo_url": "https://images.unsplash.com/photo-1589941013453-ec89f33b5e95"
    },
    {
        "_id": "pet_dog_008",
        "name": "Rosie",
        "species": "dog",
        "breed": "Beagle",
        "age_months": 15,
        "gender": "Female",
        "size": "small",
        "energy_level": 3,
        "good_with_kids": True,
        "good_with_other_pets": True,
        "temperament": ["Curious", "Merry", "Friendly", "Food Motivated"],
        "housing_requirement": "apartment_or_house",
        "bio_text": "A curious sniffer whose nose leads every adventure. Enjoys family outings, neighborhood sniffing expeditions, and crunchy healthy treats.",
        "quirks": ["Nose never leaves the grass on trail walks", "Soft baying when dinner bowls clink"],
        "exercise_needs": "45-60 minutes exploratory scent walks",
        "triggers": ["Unsecured kitchen trash bins"],
        "photo_url": "https://images.unsplash.com/photo-1505628346881-b72b27e84530"
    },
    {
        "_id": "pet_dog_009",
        "name": "Teddy",
        "species": "dog",
        "breed": "Poodle (Standard)",
        "age_months": 36,
        "gender": "Male",
        "size": "large",
        "energy_level": 3,
        "good_with_kids": True,
        "good_with_other_pets": True,
        "temperament": ["Hypoallergenic", "Gentle", "Clever", "Poised"],
        "housing_requirement": "apartment_or_house",
        "bio_text": "Hypoallergenic champion with graceful manners and an affectionate personality. Does not shed fur, ideal for allergy-conscious homes.",
        "quirks": ["Daintily steps over water puddles", "Loves puzzle feeder toys"],
        "exercise_needs": "45-60 minutes daily walks and retrieve games",
        "triggers": ["Overdue coat grooming"],
        "photo_url": "https://images.unsplash.com/photo-1608096299210-db7e38487075"
    },
    {
        "_id": "pet_dog_010",
        "name": "Chloe",
        "species": "dog",
        "breed": "Dachshund (Miniature)",
        "age_months": 20,
        "gender": "Female",
        "size": "small",
        "energy_level": 3,
        "good_with_kids": False,
        "good_with_other_pets": True,
        "temperament": ["Spunky", "Brave", "Playful", "Loyal"],
        "housing_requirement": "apartment",
        "bio_text": "Little sausage with a mighty personality! Adores burrowing deep under fleece blankets and keeping watch from the living room sofa.",
        "quirks": ["Burrows like a mole under every bed duvet", "Stands on hind legs begging for ear rubs"],
        "exercise_needs": "30 minutes daily strolls, avoiding high jumping",
        "triggers": ["Rough handling of back/spine by small kids"],
        "photo_url": "https://images.unsplash.com/photo-1612195583950-b8fd34c87093"
    },
    {
        "_id": "pet_dog_011",
        "name": "Buster",
        "species": "dog",
        "breed": "Australian Cattle Dog",
        "age_months": 22,
        "gender": "Male",
        "size": "medium",
        "energy_level": 5,
        "good_with_kids": False,
        "good_with_other_pets": False,
        "temperament": ["Tough", "Laser Focused", "Active", "Brave"],
        "housing_requirement": "house_with_yard",
        "bio_text": "High-octane athlete built for endurance running, farm life, or competitive agility sports. Requires an active lifestyle partner.",
        "quirks": ["Catches frisbees mid-air with acrobatic flips", "Herds rolling soccer balls"],
        "exercise_needs": "90+ minutes intense activity and agility workouts",
        "triggers": ["Fast bicycles zipping past unpredictably"],
        "photo_url": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119"
    },
    {
        "_id": "pet_dog_012",
        "name": "Penny",
        "species": "dog",
        "breed": "Cocker Spaniel",
        "age_months": 40,
        "gender": "Female",
        "size": "medium",
        "energy_level": 3,
        "good_with_kids": True,
        "good_with_other_pets": True,
        "temperament": ["Merry", "Sweet", "Sensitive", "Eager to Please"],
        "housing_requirement": "apartment_or_house",
        "bio_text": "A sweet, gentle soul with amber eyes. She enjoys calm nature trails, splashing in shallow creeks, and snuggle sessions on the rug.",
        "quirks": ["Splashes paws excitedly in puddles", "Resting head on people's palms"],
        "exercise_needs": "45 minutes daily walking and swimming when available",
        "triggers": ["Very loud fireworks"],
        "photo_url": "https://images.unsplash.com/photo-1548199973-03cce0bbc87b"
    },
    {
        "_id": "pet_dog_013",
        "name": "Samson",
        "species": "dog",
        "breed": "Bernese Mountain Dog",
        "age_months": 32,
        "gender": "Male",
        "size": "large",
        "energy_level": 2,
        "good_with_kids": True,
        "good_with_other_pets": True,
        "temperament": ["Gentle Giant", "Calm", "Good Natured", "Patient"],
        "housing_requirement": "house_with_yard",
        "bio_text": "A majestic gentle giant with tri-color beauty. Incredibly patient with kids and calm around other pets; loves cool fall and winter weather.",
        "quirks": ["Leans his whole 100-lb body against your legs in affection", "Loves lying on snowy patches"],
        "exercise_needs": "40 minutes steady morning and evening walks",
        "triggers": ["High summer heat and humidity"],
        "photo_url": "https://images.unsplash.com/photo-1517849845537-4d257902454a"
    },
    {
        "_id": "pet_dog_014",
        "name": "Jax",
        "species": "dog",
        "breed": "Jack Russell Terrier",
        "age_months": 16,
        "gender": "Male",
        "size": "small",
        "energy_level": 5,
        "good_with_kids": True,
        "good_with_other_pets": False,
        "temperament": ["Feisty", "Fearless", "Energetic", "Clever"],
        "housing_requirement": "apartment_or_house",
        "bio_text": "Pocket rocket full of fun and determination. Can jump three feet straight in the air and loves obstacle courses and squeaky rubber balls.",
        "quirks": ["Spring-loaded jumps when leashes are touched", "Shakes squeaky toys triumphantly"],
        "exercise_needs": "60 minutes high-tempo exercise plus fetch",
        "triggers": ["Hamsters, guinea pigs, or small rodents"],
        "photo_url": "https://images.unsplash.com/photo-1546527868-ccb7ee7dfa6a"
    },
    {
        "_id": "pet_dog_015",
        "name": "Stella",
        "species": "dog",
        "breed": "Great Dane",
        "age_months": 50,
        "gender": "Female",
        "size": "large",
        "energy_level": 2,
        "good_with_kids": True,
        "good_with_other_pets": True,
        "temperament": ["Quiet", "Couch Potato", "Gentle", "Docile"],
        "housing_requirement": "apartment_or_house",
        "bio_text": "Surprising couch potato despite her regal size. Quiet indoors, rarely barks, and will claim any extra-large dog bed as her personal throne.",
        "quirks": ["Thinks she is a miniature lap dog", "Graceful slow-motion stretching sessions"],
        "exercise_needs": "30-40 minutes calm paced neighborhood walks",
        "triggers": ["Slippery slick tile flooring without rugs"],
        "photo_url": "https://images.unsplash.com/photo-1544568100-847a948585b9"
    },
    {
        "_id": "pet_dog_016",
        "name": "Pip",
        "species": "dog",
        "breed": "Chihuahua Mix",
        "age_months": 60,
        "gender": "Male",
        "size": "small",
        "energy_level": 2,
        "good_with_kids": False,
        "good_with_other_pets": True,
        "temperament": ["Loyal", "Sensitive", "Quiet", "Attached"],
        "housing_requirement": "apartment",
        "bio_text": "Tiny senior fellow looking for a peaceful adult sanctuary. Once he bonds, he becomes your unwavering shadow and cardigan-tucked companion.",
        "quirks": ["Sleeps inside sweater pockets or tote bags", "Sunbathes through windowpanes"],
        "exercise_needs": "15-20 minutes quiet sidewalk strolls",
        "triggers": ["Unannounced strangers reaching directly over his head"],
        "photo_url": "https://images.unsplash.com/photo-1561037404-61cd46aa615b"
    },
    {
        "_id": "pet_dog_017",
        "name": "Kona",
        "species": "dog",
        "breed": "Labrador Retriever",
        "age_months": 20,
        "gender": "Female",
        "size": "large",
        "energy_level": 4,
        "good_with_kids": True,
        "good_with_other_pets": True,
        "temperament": ["Social", "Water Lover", "Friendly", "Enthusiastic"],
        "housing_requirement": "apartment_or_house",
        "bio_text": "Chocolate bundle of optimism! Loves every human she meets, adores swimming in lakes, and is an enthusiastic hiking partner for families.",
        "quirks": ["Carries your clean socks as welcoming gifts", "Cannot pass any puddle without dipping toes"],
        "exercise_needs": "60 minutes daily walks, retrieval, and dock swimming",
        "triggers": ["None noted - very resilient temperament"],
        "photo_url": "https://images.unsplash.com/photo-1529429617124-95b104e86bcd"
    },
    {
        "_id": "pet_dog_018",
        "name": "Gus",
        "species": "dog",
        "breed": "Basset Hound",
        "age_months": 45,
        "gender": "Male",
        "size": "medium",
        "energy_level": 1,
        "good_with_kids": True,
        "good_with_other_pets": True,
        "temperament": ["Easygoing", "Placid", "Affectionate", "Slow Paced"],
        "housing_requirement": "apartment",
        "bio_text": "Low rider with long velvety ears and a zen outlook on life. Prefers smelling flowers slowly to hurried jogs. Great for relaxed households.",
        "quirks": ["Trips gently over his own ears during puppy trots", "Melts into a puddle of contentment when scratched behind ears"],
        "exercise_needs": "20 minutes slow scent amble",
        "triggers": ["Being rushed during bathroom walks"],
        "photo_url": "https://images.unsplash.com/photo-1546975490-e8b92a360b24"
    },
    # ── Cats & Felines ───────────────────────────────────────────────
    {
        "_id": "pet_cat_019",
        "name": "Oliver",
        "species": "cat",
        "breed": "Domestic Shorthair",
        "age_months": 24,
        "gender": "Male",
        "size": "medium",
        "energy_level": 2,
        "good_with_kids": True,
        "good_with_other_pets": True,
        "temperament": ["Curious", "Affectionate", "Adaptable", "Friendly"],
        "housing_requirement": "apartment",
        "bio_text": "Orange tabby sweetheart who greets you at the apartment door with melodic chirps. Loves feather wands, laser chases, and warm lap snuggles.",
        "quirks": ["Greets you with upright tail and headbutts", "Chats with outside birds through glass"],
        "exercise_needs": "15 minutes interactive feather wand play daily",
        "triggers": ["Aerosol spray bottles"],
        "photo_url": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba"
    },
    {
        "_id": "pet_cat_020",
        "name": "Cleo",
        "species": "cat",
        "breed": "Siamese",
        "age_months": 36,
        "gender": "Female",
        "size": "small",
        "energy_level": 4,
        "good_with_kids": True,
        "good_with_other_pets": True,
        "temperament": ["Vocal", "Social", "Inquisitive", "Bonded"],
        "housing_requirement": "apartment_or_house",
        "bio_text": "Graceful blue-eyed conversationalist. She wants to be involved in everything you do—from laptop typing to supervising dinner preparation.",
        "quirks": ["Has a distinct vocal tone for every situation", "Rides on human shoulders around the house"],
        "exercise_needs": "30 minutes daily climbing and puzzle ball hunting",
        "triggers": ["Closed bedroom doors"],
        "photo_url": "https://images.unsplash.com/photo-1513360309081-38a60b9d997c"
    },
    {
        "_id": "pet_cat_021",
        "name": "Shadow",
        "species": "cat",
        "breed": "Bombay Cat",
        "age_months": 48,
        "gender": "Male",
        "size": "medium",
        "energy_level": 2,
        "good_with_kids": False,
        "good_with_other_pets": False,
        "temperament": ["Quiet", "Independent", "Observant", "Gentle"],
        "housing_requirement": "apartment",
        "bio_text": "Sleek mini-panther who values a peaceful, calm environment. He takes a few days to warm up, then becomes a loyal nighttime cuddle companion.",
        "quirks": ["Disappears into high cat shelves during visitors", "Purrs like an engine at midnight"],
        "exercise_needs": "10-15 minutes gentle catnip toy tossing",
        "triggers": ["Loud parties, barking dogs, sudden high-pitched cries"],
        "photo_url": "https://images.unsplash.com/photo-1573865526739-10659fec78a5"
    },
    {
        "_id": "pet_cat_022",
        "name": "Bella",
        "species": "cat",
        "breed": "Ragdoll",
        "age_months": 18,
        "gender": "Female",
        "size": "large",
        "energy_level": 1,
        "good_with_kids": True,
        "good_with_other_pets": True,
        "temperament": ["Placid", "Floppy", "Sweet", "Cuddle Bug"],
        "housing_requirement": "apartment_or_house",
        "bio_text": "True to her breed, she goes completely limp in your arms when held. Incredibly sweet, gentle with children, and peaceful with dogs.",
        "quirks": ["Sleeps flat on her back on the coffee table", "Follows family members from room to room"],
        "exercise_needs": "15 minutes relaxed string chasing",
        "triggers": ["Being left outdoors (strictly indoor cat)"],
        "photo_url": "https://images.unsplash.com/photo-1533738363-b7f9aef128ce"
    },
    {
        "_id": "pet_cat_023",
        "name": "Jasper",
        "species": "cat",
        "breed": "Maine Coon",
        "age_months": 30,
        "gender": "Male",
        "size": "large",
        "energy_level": 3,
        "good_with_kids": True,
        "good_with_other_pets": True,
        "temperament": ["Gentle Giant", "Playful", "Water Friendly", "Affectionate"],
        "housing_requirement": "apartment_or_house",
        "bio_text": "Fluffy forest giant with lynx tips on his ears and a bushy tail. Loves playing with water trickling from bathroom faucets and fetching hair ties.",
        "quirks": ["Dips paws into water bowls before drinking", "Trills like a bird instead of meowing"],
        "exercise_needs": "25 minutes climbing cat trees and playing fetch",
        "triggers": ["Matted fur if not brushed weekly"],
        "photo_url": "https://images.unsplash.com/photo-1548802673-380ab8ebc7b7"
    },
    {
        "_id": "pet_cat_024",
        "name": "Mimi",
        "species": "cat",
        "breed": "Russian Blue",
        "age_months": 60,
        "gender": "Female",
        "size": "medium",
        "energy_level": 2,
        "good_with_kids": True,
        "good_with_other_pets": True,
        "temperament": ["Calm", "Low Shedding", "Polite", "Affectionate"],
        "housing_requirement": "apartment",
        "bio_text": "Silvery beauty with emerald green eyes. Produces lower glycoprotein levels, making her well-suited for mild pet allergy sufferers.",
        "quirks": ["Nudges your phone out of the way for forehead kisses", "Sits upright like a miniature statue"],
        "exercise_needs": "15 minutes chasing laser pointers",
        "triggers": ["Disruptive furniture rearranges"],
        "photo_url": "https://images.unsplash.com/photo-1518791841217-8f162f1e1131"
    },
    {
        "_id": "pet_cat_025",
        "name": "Leo",
        "species": "cat",
        "breed": "Bengal",
        "age_months": 14,
        "gender": "Male",
        "size": "medium",
        "energy_level": 5,
        "good_with_kids": True,
        "good_with_other_pets": True,
        "temperament": ["Wild Energy", "Agile", "Water Fan", "Curious"],
        "housing_requirement": "house_with_yard",
        "bio_text": "Stunning rosette coat with the agility of an Olympic gymnast. Loves running on cat exercise wheels, jumping atop refrigerators, and bath water.",
        "quirks": ["Voluntarily jumps into empty bathtubs to bat at drops", "Solves complex treat puzzle boxes in seconds"],
        "exercise_needs": "45 minutes high-energy wand sessions and climbing routes",
        "triggers": ["Confined spaces without vertical climbing trees"],
        "photo_url": "https://images.unsplash.com/photo-1513245543132-31f507417b26"
    },
    {
        "_id": "pet_cat_026",
        "name": "Chloe",
        "species": "cat",
        "breed": "Scottish Fold",
        "age_months": 26,
        "gender": "Female",
        "size": "small",
        "energy_level": 2,
        "good_with_kids": True,
        "good_with_other_pets": True,
        "temperament": ["Sweet", "Calm", "Quirky", "Affectionate"],
        "housing_requirement": "apartment",
        "bio_text": "Round owl-like face with adorable folded ears. She loves sitting like a tiny human on her hind legs (the 'Buddha pose') and watching people cook.",
        "quirks": ["Regularly sits in full Buddha pose on rugs", "Naps curled in laundry baskets"],
        "exercise_needs": "15-20 minutes daily play with soft plush mice",
        "triggers": ["Rough tail handling"],
        "photo_url": "https://images.unsplash.com/photo-1543852786-1cf6624b9987"
    },
    {
        "_id": "pet_cat_027",
        "name": "Smokey",
        "species": "cat",
        "breed": "British Shorthair",
        "age_months": 54,
        "gender": "Male",
        "size": "large",
        "energy_level": 1,
        "good_with_kids": True,
        "good_with_other_pets": True,
        "temperament": ["Dignified", "Placid", "Independent", "Easygoing"],
        "housing_requirement": "apartment",
        "bio_text": "Chubby cheeks and plush blue-grey coat. He prefers relaxing nearby rather than being continuously carried, making him an easygoing flatmate.",
        "quirks": ["Maintains regal composure while sleeping upside down", "Gently taps your arm when hungry"],
        "exercise_needs": "15 minutes interactive ball track play",
        "triggers": ["Being carried like a baby for prolonged periods"],
        "photo_url": "https://images.unsplash.com/photo-1506755855567-92ff770e8d00"
    },
    {
        "_id": "pet_cat_028",
        "name": "Willow",
        "species": "cat",
        "breed": "Persian",
        "age_months": 42,
        "gender": "Female",
        "size": "medium",
        "energy_level": 1,
        "good_with_kids": False,
        "good_with_other_pets": True,
        "temperament": ["Serene", "Quiet", "Aristocratic", "Sweet"],
        "housing_requirement": "apartment",
        "bio_text": "Serene cloud of white fur with a sweet, quiet demeanor. Requires daily brushing and a quiet, low-stress home without rambunctious toddlers.",
        "quirks": ["Eats kibble one piece at a time with polite delicacy", "Loves silk pillows and soft rugs"],
        "exercise_needs": "10 minutes gentle batting at wool balls",
        "triggers": ["Chaotic noise, sudden toddler grabs"],
        "photo_url": "https://images.unsplash.com/photo-1518791841217-8f162f1e1131"
    },
    # ── Additional Diverse Pets (35+ total) ───────────────────────────
    {
        "_id": "pet_dog_029",
        "name": "Archie",
        "species": "dog",
        "breed": "Corgi (Pembroke Welsh)",
        "age_months": 20,
        "gender": "Male",
        "size": "small",
        "energy_level": 4,
        "good_with_kids": True,
        "good_with_other_pets": True,
        "temperament": ["Bold", "Outgoing", "Playful", "Spirited"],
        "housing_requirement": "apartment_or_house",
        "bio_text": "Cheerful loaf with charismatic bat ears and stubby legs. Full of big-dog attitude in an apartment-manageable size, loves neighborhood walks.",
        "quirks": ["Splooting legs straight back when cooling on hardwood", "Barks once proudly after finishing meals"],
        "exercise_needs": "45-60 minutes brisk daily walks and herding ball games",
        "triggers": ["Vacuum cleaner monsters"],
        "photo_url": "https://images.unsplash.com/photo-1612536057832-2ff7ead58194"
    },
    {
        "_id": "pet_dog_030",
        "name": "Nova",
        "species": "dog",
        "breed": "Australian Shepherd",
        "age_months": 26,
        "gender": "Female",
        "size": "medium",
        "energy_level": 5,
        "good_with_kids": True,
        "good_with_other_pets": True,
        "temperament": ["Athletic", "Loyal", "Vibrant", "Protective"],
        "housing_requirement": "house_with_yard",
        "bio_text": "Striking blue merle coat with boundless energy and loyalty. An ideal partner for long distance runners, outdoor trail blazers, and campers.",
        "quirks": ["Does precision spin-tricks before catching treats", "Watches TV animal documentaries intently"],
        "exercise_needs": "80+ minutes trail running and brain puzzles daily",
        "triggers": ["Lack of mental stimulation causes herding behavior"],
        "photo_url": "https://images.unsplash.com/photo-1503256207526-0d5d80fa2f47"
    },
    {
        "_id": "pet_dog_031",
        "name": "Waffles",
        "species": "dog",
        "breed": "Pug",
        "age_months": 34,
        "gender": "Male",
        "size": "small",
        "energy_level": 2,
        "good_with_kids": True,
        "good_with_other_pets": True,
        "temperament": ["Charming", "Affectionate", "Mischievous", "Loving"],
        "housing_requirement": "apartment",
        "bio_text": "Charming clown whose sole purpose in life is making people smile and collecting tummy rubs. Great in apartments with minimal exercise requirements.",
        "quirks": ["Does an excited happy-dance whenever someone enters the room", "Snores like a tiny outboard motor"],
        "exercise_needs": "20 minutes light stroll in cool parts of the day",
        "triggers": ["Hot humid weather (brachycephalic)"],
        "photo_url": "https://images.unsplash.com/photo-1517849845537-4d257902454a"
    },
    {
        "_id": "pet_dog_032",
        "name": "Hazel",
        "species": "dog",
        "breed": "Whippet",
        "age_months": 22,
        "gender": "Female",
        "size": "medium",
        "energy_level": 3,
        "good_with_kids": True,
        "good_with_other_pets": True,
        "temperament": ["Gentle", "Quiet", "Sprinter", "Apartment Friendly"],
        "housing_requirement": "apartment_or_house",
        "bio_text": "The perfect blend of zoomies and naps. Does a 5-minute high-speed sprint across grass, then spends the next 8 hours curled up under a warm blanket.",
        "quirks": ["Virtually silent—never barks at postal workers", "Shivers politely asking for her winter fleece coat"],
        "exercise_needs": "35 minutes daily walk plus an enclosed sprint session",
        "triggers": ["Off-leash areas without secure perimeter fencing (sighthound prey drive)"],
        "photo_url": "https://images.unsplash.com/photo-1544568100-847a948585b9"
    },
    {
        "_id": "pet_dog_033",
        "name": "Diesel",
        "species": "dog",
        "breed": "Rottweiler",
        "age_months": 38,
        "gender": "Male",
        "size": "large",
        "energy_level": 3,
        "good_with_kids": True,
        "good_with_other_pets": False,
        "temperament": ["Calm", "Confident", "Courageous", "Loyal"],
        "housing_requirement": "house_with_yard",
        "bio_text": "Calm, steadfast protector who forms an unbreakable bond with his family. Very well-mannered on walks, loves relaxing by your chair in the evenings.",
        "quirks": ["Produces a low contented purr-rumble during neck massages", "Loves carrying giant tree branches"],
        "exercise_needs": "50 minutes structured exercise and scent work",
        "triggers": ["Unfamiliar off-leash dogs charging up rudely"],
        "photo_url": "https://images.unsplash.com/photo-1567752881298-894bb81f9379"
    },
    {
        "_id": "pet_cat_034",
        "name": "Nala",
        "species": "cat",
        "breed": "Abyssinian",
        "age_months": 19,
        "gender": "Female",
        "size": "small",
        "energy_level": 4,
        "good_with_kids": True,
        "good_with_other_pets": True,
        "temperament": ["Athletic", "Extroverted", "Playful", "Curious"],
        "housing_requirement": "apartment_or_house",
        "bio_text": "Warm ruddy coat resembling an African wildcat. Constantly in motion, discovering high perches, and investigating every corner of your home.",
        "quirks": ["Perches right on door tops like a gargoyle", "Plays fetch with soft foam balls"],
        "exercise_needs": "30 minutes energetic interactive toy games",
        "triggers": ["Being confined to a single closed bedroom"],
        "photo_url": "https://images.unsplash.com/photo-1513360309081-38a60b9d997c"
    },
    {
        "_id": "pet_cat_035",
        "name": "Simba",
        "species": "cat",
        "breed": "Ginger Tabby Mix",
        "age_months": 72,
        "gender": "Male",
        "size": "large",
        "energy_level": 1,
        "good_with_kids": True,
        "good_with_other_pets": True,
        "temperament": ["Mellow", "Gentle", "Couch Companion", "Friendly"],
        "housing_requirement": "apartment",
        "bio_text": "Senior gent with big golden eyes and infinite patience. Never causes trouble, loves curling on the bed during thunderstorms, and purrs continuously.",
        "quirks": ["Falls asleep halfway through self-grooming sessions", "Gentle headbutts when you prepare coffee"],
        "exercise_needs": "10 minutes casual batting at catnip mice",
        "triggers": ["None - exceptionally unflappable senior cat"],
        "photo_url": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba"
    },
    {
        "_id": "pet_dog_036",
        "name": "Pepper",
        "species": "dog",
        "breed": "Miniature Schnauzer",
        "age_months": 28,
        "gender": "Female",
        "size": "small",
        "energy_level": 3,
        "good_with_kids": True,
        "good_with_other_pets": True,
        "temperament": ["Alert", "Friendly", "Hypoallergenic", "Smart"],
        "housing_requirement": "apartment_or_house",
        "bio_text": "Distinguished little lady with fabulous whiskers and bushy eyebrows. Low-shedding hypoallergenic coat, smart as a whip, and loves agility tricks.",
        "quirks": ["Cocky little head-tilt when asked 'Do you want a treat?'", "Groomed beard gets wiped on rugs after drinking"],
        "exercise_needs": "40 minutes daily walks and interactive obedience tricks",
        "triggers": ["Doorbell chimes initiate alert barking"],
        "photo_url": "https://images.unsplash.com/photo-1583511655857-d19b40a7a54e"
    }
]


def create_pet_embedding_text(pet: Dict[str, Any]) -> str:
    """
    Constructs a rich narrative document representation for semantic vector search.
    Enriches with species, breed, energy, temperament, quirks, exercise needs, and bio.
    """
    temperament_str = ", ".join(pet.get("temperament", []))
    quirks_str = "; ".join(pet.get("quirks", []))
    triggers_str = "; ".join(pet.get("triggers", []))

    return (
        f"Species: {pet.get('species')}. "
        f"Breed: {pet.get('breed')}. "
        f"Age: {pet.get('age_months')} months. Gender: {pet.get('gender')}. "
        f"Size: {pet.get('size')}. Energy Level: {pet.get('energy_level')}/5. "
        f"Housing: {pet.get('housing_requirement')}. "
        f"Good with kids: {pet.get('good_with_kids')}. Good with other pets: {pet.get('good_with_other_pets')}. "
        f"Temperament: {temperament_str}. "
        f"Bio: {pet.get('bio_text')} "
        f"Quirks: {quirks_str}. "
        f"Exercise needs: {pet.get('exercise_needs')}. "
        f"Triggers: {triggers_str}."
    )


def seed_database(skip_if_exists: bool = False) -> int:
    """
    Main seeding routine:
    1. Sets up standard MongoDB indexes (species, energy_level, good_with_kids, etc.)
    2. Configures Atlas Vector Search index definition
    3. Generates 768-dim embeddings for all 36 pets
    4. Upserts records into the 'pets' collection
    """
    db = get_sync_db()
    pets_col = db["pets"]

    logger.info("Setting up database indexes...")
    setup_standard_indexes(db)
    setup_atlas_vector_search_index(db)

    count_existing = pets_col.count_documents({})
    logger.info("Found %d existing pet records in MongoDB.", count_existing)

    if skip_if_exists and count_existing >= len(RAW_PET_RECORDS):
        logger.info("Database already seeded with %d records. Skipping.", count_existing)
        return count_existing

    logger.info("Starting embedding generation for %d realistic pets...", len(RAW_PET_RECORDS))

    inserted_count = 0
    for idx, pet_data in enumerate(RAW_PET_RECORDS):
        pet_id = pet_data["_id"]
        embedding_text = create_pet_embedding_text(pet_data)

        # Check if already has embedding in db to avoid re-calling API
        existing_doc = pets_col.find_one({"_id": pet_id}, {"embedding": 1})
        if existing_doc and existing_doc.get("embedding") and len(existing_doc["embedding"]) == 768:
            logger.info("[%d/%d] Reusing existing 768-dim embedding for %s (%s)", idx + 1, len(RAW_PET_RECORDS), pet_data["name"], pet_id)
            pet_data["embedding"] = existing_doc["embedding"]
        else:
            logger.info("[%d/%d] Generating 768-dim vector for %s (%s)...", idx + 1, len(RAW_PET_RECORDS), pet_data["name"], pet_id)
            pet_data["embedding"] = generate_embedding(embedding_text)

        # Validate with Pydantic model
        validated_pet = Pet(**pet_data)

        # Upsert into MongoDB
        pets_col.update_one(
            {"_id": validated_pet.id},
            {"$set": validated_pet.model_dump(by_alias=True)},
            upsert=True
        )
        inserted_count += 1

    total_in_db = pets_col.count_documents({})
    logger.info("Seeding completed successfully! Total pets in database: %d", total_in_db)
    return total_in_db


if __name__ == "__main__":
    seed_database()

