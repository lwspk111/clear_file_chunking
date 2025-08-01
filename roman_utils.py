class RomanNum:
    """罗马数字处理工具类"""
    
    def IntToRoman(num: int) -> str:
        values = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        symbols = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
        small_symbols = ["m", "cm", "d", "cd", "c", "xc", "l", "xl", "x", "ix","v","iv","i"]
        roman = ''
        small_roman = ''
        i = 0
        while num > 0:
            k = num // values[i]
            for j in range(k):
                roman += symbols[i]
                small_roman += small_symbols[i]
                num -= values[i]
            i += 1

        return [roman, small_roman]

    def generate_roman_numerals(limit: int) -> set:
        """Generates a set of Roman numerals up to a given limit."""
        roman_numerals = set()
        for i in range(1, limit + 1):
            romans = RomanNum.IntToRoman(i)
            roman_numerals.add(romans[0])  # Uppercase
            roman_numerals.add(romans[1])  # Lowercase
        return roman_numerals

    # Unicode Roman numerals to ASCII mapping
    UNICODE_ROMAN_MAP = {
        'Ⅰ': 'I', 'Ⅱ': 'II', 'Ⅲ': 'III', 'Ⅳ': 'IV', 'Ⅴ': 'V', 'Ⅵ': 'VI', 'Ⅶ': 'VII', 'Ⅷ': 'VIII', 'Ⅸ': 'IX', 'Ⅹ': 'X', 'Ⅺ': 'XI', 'Ⅻ': 'XII',
        'ⅰ': 'i', 'ⅱ': 'ii', 'ⅲ': 'iii', 'ⅳ': 'iv', 'ⅴ': 'v', 'ⅵ': 'vi', 'ⅶ': 'vii', 'ⅷ': 'viii', 'ⅸ': 'ix', 'ⅹ': 'x', 'ⅺ': 'xi', 'ⅻ': 'xii',
        'Ⅼ': 'L', 'Ⅽ': 'C', 'Ⅾ': 'D', 'Ⅿ': 'M',
        'ⅼ': 'l', 'ⅽ': 'c', 'ⅾ': 'd', 'ⅿ': 'm'
    }

    def normalize_roman_numerals(text: str) -> str:
        """Replaces Unicode Roman numerals with their ASCII equivalents."""
        for uni, asc in RomanNum.UNICODE_ROMAN_MAP.items():
            text = text.replace(uni, asc)
        return text

# 生成罗马数字集合
ROMAN_NUMERALS = RomanNum.generate_roman_numerals(50) 