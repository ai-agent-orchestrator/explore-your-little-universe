"""Rider-Waite-style names; symbolic editorial mappings, not predictions."""
from dataclasses import dataclass

ORIENTATIONS = ('upright', 'reversed')
POSITIONS = ('past', 'present', 'future')
SUIT_ELEMENTS = {'wands':'fire','cups':'water','swords':'air','pentacles':'earth'}
MAJORS = [
    ('fool','바보'),('magician','마법사'),('high-priestess','여사제'),('empress','여황제'),
    ('emperor','황제'),('hierophant','교황'),('lovers','연인'),('chariot','전차'),
    ('strength','힘'),('hermit','은둔자'),('wheel-of-fortune','운명의 수레바퀴'),
    ('justice','정의'),('hanged-man','매달린 사람'),('death','죽음'),('temperance','절제'),
    ('devil','악마'),('tower','탑'),('star','별'),('moon','달'),('sun','태양'),
    ('judgement','심판'),('world','세계'),
]
RANKS = ['ace','two','three','four','five','six','seven','eight','nine','ten','page','knight','queen','king']
RANK_NAMES = ['에이스','2','3','4','5','6','7','8','9','10','시종','기사','여왕','왕']
SUIT_NAMES = {'wands':'완드','cups':'컵','swords':'소드','pentacles':'펜타클'}

@dataclass(frozen=True)
class TarotCard:
    card_id: str
    arcana: str
    suit: str
    rank: int
    name_ko: str
    name_en: str
    element: str | None

CARDS = tuple([TarotCard(f'major-{i:02}-{slug}','major','',i,name,slug.replace('-',' ').title(),None)
               for i,(slug,name) in enumerate(MAJORS)] +
              [TarotCard(f'{suit}-{i:02}-{rank}','minor',suit,i,f'{SUIT_NAMES[suit]} {RANK_NAMES[i-1]}',
                         f'{rank.title()} of {suit.title()}',element)
               for suit,element in SUIT_ELEMENTS.items() for i,rank in enumerate(RANKS,1)])
BY_ID = {card.card_id:card for card in CARDS}

def meanings():
    return [{'meaning_id':f'{card.card_id}:{orientation}','card_id':card.card_id,'orientation':orientation}
            for card in CARDS for orientation in ORIENTATIONS]
