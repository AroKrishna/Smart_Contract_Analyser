"""
analysis/parser.py - Pure Python Solidity Structural and NatSpec Parser

Provides line-accurate extraction of contracts, functions, state variables,
modifiers, and NatSpec annotations without requiring external solc binaries.
"""

import re
from typing import List, Dict, Any, Optional

class SolidityParser:
    def __init__(self, source_code: str):
        self.source_code = source_code
        self.lines = source_code.splitlines()
        self.warnings: List[str] = []
        self.errors: List[str] = []

    def parse(self) -> Dict[str, Any]:
        """Parses the Solidity source into structural components with line numbers."""
        if not self.source_code.strip():
            return {
                "status": "empty_input",
                "pragmas": [],
                "contracts": [],
                "warnings": ["Source code is empty."],
                "total_lines": 0
            }

        try:
            pragmas = self._extract_pragmas()
            contracts = self._extract_contracts()
            
            return {
                "status": "success",
                "pragmas": pragmas,
                "contracts": contracts,
                "warnings": self.warnings,
                "total_lines": len(self.lines)
            }
        except Exception as e:
            return {
                "status": "malformed_input",
                "pragmas": [],
                "contracts": [],
                "warnings": self.warnings + [f"Parsing error: {str(e)}"],
                "total_lines": len(self.lines)
            }

    def _extract_pragmas(self) -> List[Dict[str, Any]]:
        results = []
        for idx, line in enumerate(self.lines, start=1):
            match = re.search(r'pragma\s+solidity\s+([^;]+);', line)
            if match:
                results.append({
                    "version": match.group(1).strip(),
                    "line": idx
                })
        return results

    def _extract_contracts(self) -> List[Dict[str, Any]]:
        """Identifies contract, interface, and library blocks and their internals."""
        contracts = []
        contract_decl_re = re.compile(
            r'^\s*(contract|abstract\s+contract|interface|library)\s+([A-Za-z0-9_]+)(?:\s+is\s+([^{]+))?\s*\{',
            re.MULTILINE
        )

        for match in contract_decl_re.finditer(self.source_code):
            kind = match.group(1).strip()
            name = match.group(2).strip()
            inheritance = [i.strip() for i in match.group(3).split(',')] if match.group(3) else []
            
            # Compute start line
            start_pos = match.start()
            start_line = self.source_code[:start_pos].count('\n') + 1
            
            # Find matching closing brace
            end_pos, end_line = self._find_closing_brace(match.end() - 1)
            contract_body = self.source_code[match.end():end_pos]
            
            # Extract contract-level NatSpec
            contract_natspec = self._extract_preceding_natspec(start_line)

            # Extract internals
            functions = self._extract_functions(contract_body, start_line)
            state_vars = self._extract_state_variables(contract_body, start_line)

            contracts.append({
                "name": name,
                "kind": kind,
                "inheritance": inheritance,
                "start_line": start_line,
                "end_line": end_line,
                "natspec": contract_natspec,
                "functions": functions,
                "state_variables": state_vars
            })

        return contracts

    def _find_closing_brace(self, open_brace_pos: int) -> tuple[int, int]:
        depth = 0
        in_line_comment = False
        in_block_comment = False
        in_string = False
        quote_char = ''

        for pos in range(open_brace_pos, len(self.source_code)):
            ch = self.source_code[pos]
            prev = self.source_code[pos - 1] if pos > 0 else ''
            nxt = self.source_code[pos + 1] if pos + 1 < len(self.source_code) else ''

            if in_line_comment:
                if ch == '\n':
                    in_line_comment = False
                continue
            if in_block_comment:
                if prev == '*' and ch == '/':
                    in_block_comment = False
                continue
            if in_string:
                if ch == quote_char and prev != '\\':
                    in_string = False
                continue

            if ch == '/' and nxt == '/':
                in_line_comment = True
                continue
            if ch == '/' and nxt == '*':
                in_block_comment = True
                continue
            if ch in ('"', "'"):
                in_string = True
                quote_char = ch
                continue

            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end_line = self.source_code[:pos].count('\n') + 1
                    return pos, end_line

        return len(self.source_code), len(self.lines)

    def _extract_functions(self, body: str, contract_start_line: int) -> List[Dict[str, Any]]:
        functions = []
        func_re = re.compile(
            r'(?:function\s+([A-Za-z0-9_]*)|(constructor|fallback|receive))\s*\(([^)]*)\)\s*([^;{]*)(?:\{|;)',
            re.MULTILINE
        )

        for match in func_re.finditer(body):
            name = match.group(1) or match.group(2) or "anonymous"
            params = match.group(3).strip()
            attributes = match.group(4).strip()
            
            # Line calculation relative to whole file
            match_start_in_source = self.source_code.find(match.group(0))
            if match_start_in_source != -1:
                func_start_line = self.source_code[:match_start_in_source].count('\n') + 1
            else:
                func_start_line = contract_start_line + body[:match.start()].count('\n')

            # Extract modifiers
            attr_tokens = [t.strip() for t in attributes.split() if t.strip()]
            visibility = 'public' # default in older versions
            mutability = 'nonpayable'
            custom_modifiers = []

            for token in attr_tokens:
                if token in ('public', 'external', 'internal', 'private'):
                    visibility = token
                elif token in ('view', 'pure', 'payable'):
                    mutability = token
                elif token not in ('returns', 'virtual', 'override'):
                    # Likely a modifier (e.g. onlyOwner, whenNotPaused)
                    clean_mod = re.sub(r'\(.*\)', '', token)
                    if clean_mod:
                        custom_modifiers.append(clean_mod)

            # Find function end
            is_implemented = match.group(0).endswith('{')
            if is_implemented:
                func_body_start = match.end() - 1
                # Local search for closing brace
                depth = 1
                end_idx = func_body_start + 1
                while depth > 0 and end_idx < len(body):
                    if body[end_idx] == '{':
                        depth += 1
                    elif body[end_idx] == '}':
                        depth -= 1
                    end_idx += 1
                func_raw = body[match.start():end_idx]
                func_end_line = func_start_line + func_raw.count('\n')
            else:
                func_raw = match.group(0)
                func_end_line = func_start_line

            # Extract preceding NatSpec
            natspec = self._extract_preceding_natspec(func_start_line)

            functions.append({
                "name": name,
                "visibility": visibility,
                "mutability": mutability,
                "modifiers": custom_modifiers,
                "params": params,
                "start_line": func_start_line,
                "end_line": func_end_line,
                "raw_code": func_raw.strip(),
                "natspec": natspec
            })

        return functions

    def _extract_state_variables(self, body: str, contract_start_line: int) -> List[Dict[str, Any]]:
        variables = []
        var_re = re.compile(
            r'^\s*(address|uint\d*|int\d*|bool|string|bytes\d*|mapping\s*\([^;]+\))\s+(public|private|internal|constant|immutable|\s*)*([A-Za-z0-9_]+)\s*(?:=\s*[^;]+)?\s*;',
            re.MULTILINE
        )

        for match in var_re.finditer(body):
            v_type = match.group(1).strip()
            attr = (match.group(2) or "").strip()
            v_name = match.group(3).strip()

            var_start_in_source = self.source_code.find(match.group(0))
            if var_start_in_source != -1:
                line_no = self.source_code[:var_start_in_source].count('\n') + 1
            else:
                line_no = contract_start_line + body[:match.start()].count('\n')

            is_public = 'public' in attr
            is_constant = 'constant' in attr or 'immutable' in attr

            variables.append({
                "name": v_name,
                "type": v_type,
                "is_public": is_public,
                "is_constant": is_constant,
                "line": line_no,
                "raw": match.group(0).strip()
            })

        return variables

    def _extract_preceding_natspec(self, target_line: int) -> Dict[str, str]:
        """Extracts NatSpec comments immediately preceding the target line."""
        natspec = {}
        idx = target_line - 2 # 0-indexed line right above
        comment_lines = []

        while idx >= 0:
            line_str = self.lines[idx].strip()
            if line_str.startswith('///') or line_str.startswith('*') or line_str.startswith('/**'):
                comment_lines.insert(0, line_str)
                idx -= 1
            elif line_str.endswith('*/'):
                comment_lines.insert(0, line_str)
                idx -= 1
            else:
                break

        full_comment = "\n".join(comment_lines)
        # Parse tags
        notice = re.search(r'@notice\s+([^\n*]+)', full_comment)
        dev = re.search(r'@dev\s+([^\n*]+)', full_comment)
        if notice:
            natspec['notice'] = notice.group(1).strip()
        if dev:
            natspec['dev'] = dev.group(1).strip()
        if full_comment:
            natspec['raw'] = full_comment

        return natspec
