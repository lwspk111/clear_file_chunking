import unicodeitplus

class FormulaProcessor:
    """数学公式处理工具类"""
    
    def is_complex_formular(text):
        """判断是否为复杂公式"""
        complex_flag = {r"\frac", r"\sqrt", r"\sum", r"\int", r"\end", r"\array", r"\begin", r"\sum", r"\prod", r"\lim"}
        # 如果有这些flag，则属于复杂公式
        if any(flag in text for flag in complex_flag):
            return True
        return False

    def restore_formular(formula):
        """恢复公式格式"""
        if FormulaProcessor.is_complex_formular(formula):
            return (formula, "complex")
        else: 
            formula = unicodeitplus.parse(formula)
            return (formula, "easy") 