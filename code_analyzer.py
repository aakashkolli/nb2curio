import ast
from functools import lru_cache
from typing import Optional, Dict, Any, Set
import pandas as pd
from .config import config
from .data_models import CellAnalysis

class RHSVariableVisitor(ast.NodeVisitor):
    """Visitor to collect variables used in right-hand side of assignments."""
    def __init__(self):
        self.used_vars = set()
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used_vars.add(node.id)

class CodeAnalyzer:
    """
    Analyzes code cells for dependencies and categorization. The AST traversal
    is now consolidated into a single pass for efficiency.
    """
    
    def __init__(self):
        self._ast_cache = {}
    
    @lru_cache(maxsize=128)
    def clean_code_for_ast(self, source: str) -> str:
        """Removes IPython magic commands and shell commands from code."""
        cleaned = config.MAGIC_PATTERN.sub('', source)
        cleaned = config.SHELL_PATTERN.sub('', cleaned)
        return cleaned
    
    def _execute_for_altair_spec(self, code_string: str) -> Optional[Dict[str, Any]]:
        """
        Dynamically executes cell code in a sandboxed environment to extract the
        spec from a generated Altair chart object.
        """
        if 'alt.Chart' not in code_string:
            return None

        try:
            import altair as alt
            from vega_datasets import data

            placeholder_df = pd.DataFrame()

            exec_namespace = {
                'alt': alt,
                'pd': pd,
                'data': data,
                'df': placeholder_df
            }
            
            tree = ast.parse(self.clean_code_for_ast(code_string))
            if not tree.body or not isinstance(tree.body[-1], ast.Expr):
                return None

            main_code_block = ast.Module(body=tree.body[:-1], type_ignores=[])
            last_expression = ast.Expression(body=tree.body[-1].value)
            
            exec(compile(main_code_block, filename='<ast>', mode='exec'), exec_namespace)
            chart_object = eval(compile(last_expression, filename='<ast>', mode='eval'), exec_namespace)

            if hasattr(chart_object, 'to_dict'):
                return chart_object.to_dict()
        except Exception:
            return None
        return None

    def analyze_dependencies(self, code_string: str) -> CellAnalysis:
        """
        Analyzes code in a single pass to find variables, dependencies,
        and categorization, including mutations and Vega-Lite specs.
        """
        cache_key = hash(code_string)
        if cache_key not in self._ast_cache:
            try:
                self._ast_cache[cache_key] = ast.parse(self.clean_code_for_ast(code_string))
            except SyntaxError as e:
                print(f"Warning: Could not parse a cell. Error: {e}")
                return CellAnalysis(set(), set(), set(), "other")

        tree = self._ast_cache[cache_key]
        defined_vars, used_vars = set(), set()
        mutated_vars, pure_overwrites = set(), set()
        imported_aliases = set()
        vega_spec = None

        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    defined_vars.add(node.id)
                elif isinstance(node.ctx, ast.Load):
                    used_vars.add(node.id)
            elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                defined_vars.add(node.name)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    imported_aliases.add(alias.asname or alias.name)
            elif isinstance(node, ast.Call):
                if any(kw.arg == 'inplace' and getattr(kw.value, 'value', False) for kw in node.keywords):
                    if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                        mutated_vars.add(node.func.value.id)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
                        mutated_vars.add(target.value.id)
                
                lhs_vars = {t.id for t in node.targets if isinstance(t, ast.Name)}
                rhs_visitor = RHSVariableVisitor()
                rhs_visitor.visit(node.value)
                pure_overwrites.update(lhs_vars - rhs_visitor.used_vars)

                if not vega_spec and any(isinstance(t, ast.Name) and t.id == 'spec' for t in node.targets):
                    try:
                        spec_dict = ast.literal_eval(node.value)
                        if isinstance(spec_dict, dict) and "$schema" in spec_dict:
                            vega_spec = spec_dict
                    except (ValueError, SyntaxError):
                        pass

        if vega_spec is None:
            vega_spec = self._execute_for_altair_spec(code_string)

        category = self._categorize_cell(tree, code_string, vega_spec)
        used_vars.update(mutated_vars)

        return CellAnalysis(
            defined_vars=defined_vars,
            used_vars=used_vars - imported_aliases,
            pure_overwrites=pure_overwrites,
            category=category,
            vega_spec=vega_spec
        )
    
    def _categorize_cell(self, tree: ast.AST, code_string: str, vega_spec: Optional[Dict]) -> str:
        """Categorizes a cell based on its content."""
        if all(isinstance(n, (ast.Import, ast.ImportFrom)) for n in tree.body):
            return "imports"
        if any(kw in code_string for kw in config.VIZ_KEYWORDS) or vega_spec is not None:
            return "visualize"
        if any(kw in code_string for kw in config.DATA_KEYWORDS):
            return "load_data"
        if any(isinstance(n, (ast.Assign, ast.Call, ast.Expr)) for n in tree.body):
            return "transform"
        return "other"
