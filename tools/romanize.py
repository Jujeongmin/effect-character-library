"""Minimal Revised-Romanization transliterator for Hangul syllables."""
CHO = ['g','kk','n','d','tt','r','m','b','pp','s','ss','','j','jj','ch','k','t','p','h']
JUNG = ['a','ae','ya','yae','eo','e','yeo','ye','o','wa','wae','oe','yo','u','wo','we','wi','yu','eu','ui','i']
JONG = ['','k','k','k','n','n','n','t','l','k','m','l','l','l','m','l','p','l','t','t','ng','t','t','k','t','p','t']

WORDS = {
    '투사체': 'projectile', '장판': 'zone', '피격': 'hit',
    '신화스킬': 'mythic', '버프': 'buff', '디버프': 'debuff',
    '기본공격': 'basic_attack', '연타': 'combo', '일격': 'heavy',
    '전체공격': 'aoe', '특수공격': 'special', '무기이펙트': 'weapon',
    '펫': 'pet', '아우라': 'aura', '캐릭터': 'character',
    '방치보상': 'idle_reward', '컨텐츠언락': 'content_unlock',
    '시즌패스': 'season_pass', '어드벤처보스': 'adventure_boss',
    '집중': 'focus', '디스펠': 'dispel', '비례데미지': 'proportional_damage',
    '토르': 'thor', '번개': 'lightning', '화살': 'arrow', '스카디': 'skadi',
    '신성아우라': 'holy_aura', '방패': 'shield', '동상': 'statue',
    '그룹': 'group', '팔레트비교': 'palette_compare',
    '이지스': 'aegis', '폭격': 'bombard', '조합자물쇠열리는': 'combine_lock_open',
    '갈색': 'brown', '월드신규이펙트': 'world_new_effect',
}

def rom_syllable(ch):
    code = ord(ch) - 0xAC00
    if not (0 <= code < 11172):
        return None
    return CHO[code // 588] + JUNG[(code % 588) // 28] + JONG[code % 28]

def romanize(text):
    for k, v in sorted(WORDS.items(), key=lambda kv: -len(kv[0])):
        text = text.replace(k, '_' + v + '_')
    out = []
    for ch in text:
        r = rom_syllable(ch)
        out.append(r if r is not None else ch)
    return ''.join(out)
