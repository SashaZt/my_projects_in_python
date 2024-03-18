from googletrans import Translator

text_original = """
    AGV Pista GP RR Iridium Carbon 2023 Helmet

    The helmet created for MotoGP™ is now available to all riders.
    The Pista GP RR is the perfect replica of the AGV helmet used by the champions of the World Motorcycle Championship in the race.
    That is why it has received the new FIM homologation, which feels the highest possible level of protection.
    It also protects against the dangerous rotational accelerations of the head. Every detail is designed for absolute performance.
    The 100% Extreme Carbon carbon fiber shell guarantees extreme lightness, so you never feel heaviness when wearing it.
    Its shapes and metal vents have been analyzed in the wind tunnel and tested by AGV athletes to achieve the best aerodynamic penetration and maximum stability at high speeds, thanks also to the innovative profile of the rear PRO spoiler.
    The Ultravision visor optical class 1 is an essential part of the protection thanks to a thickness of 5 mm and allows a panoramic view of 190 °.
    It means seeing the track, opponents and obstacles more clearly and in front of everyone. The exclusive 360° Adaptive Fit system allows complete personalization of the interior and gives the possibility to select the ideal thickness in the upper part of the head, neck and cheeks.
    A basic comfort to literally clear your head and think only about the track.
    Every detail is designed to win. This is the perfection of obsession.

    Features:
    Removable PRO spoiler
    Racing fit
    2Dry: instant sweat absorption
    Three-piece adaptive head pad
    Adaptive 360° fit
    Safety release system for cheek pads
    Cheek pads: Shalimar fabric for a soft and stable fit even at high speed
    Head pad: elastic and breathable microfiber
    Curved neck protection profile
    Microsense: premium skin comfort
    Neck roll: breathable fabric with elastic and waterproof inserts
    Seamless in sensitive areas
    Removable and washable lining
    Removable nose guard
    Removable windshield
    2 rear vents and 5 front vents
    Metal vents and air outlets
    190° horizontal field of view
    85° vertical field of view
    5 mm visor thickness
    optics class 1
    scratch resistant visor
    metal visor mechanism
    patented additional visor quick change system
    patented visor locking system

    Specifications:
    100% carbon fiber
    titanium double D-ring closure
    5-density EPS in 4 shell sizes
    Shell and EPS structure to minimize rotational acceleration
    (FIM homologated) ECE 2206
    Weight: 1450 g (+/- 50g)

    Contents:
    1 x AGV Pista GP RR helmet
    1 x fitting kit inner part (upper head pad, neck pad, cheek pads)
    1 x hydration system
    1 x 100% Max Vision Pinlock (120)
    1 x tear-off film kit
    incl. earplugs
    incl. ventilation covers
    """
translator = Translator()
translation_uk = translator.translate(text=text_original, src='en', dest='uk').text.replace('\r\n', ' ')
print(translation_uk)
