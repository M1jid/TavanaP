import re

class QueryGenerator:

    @staticmethod
    def build_bool_query(elements, operator):
        operator_map = {'+': 'must', '|': 'should'}

        return {
            "bool": {
                operator_map[operator]: [
                    {"match_phrase": {"MESSAGE": el}} if isinstance(el, str) else el
                    for el in elements
                ]
            }
        }

    @staticmethod
    def build_query(text):
        token_pattern = r"\(|\)|\+|\||\-|[\u0600-\u06FFa-zA-Z0-9\s\u200C]+"
        tokens = re.findall(token_pattern, text)
        stack = []

        if len(tokens) == 1:
            return {"match_phrase": {"MESSAGE": tokens[0]}}

        for token in tokens:
            if token == ')':
                parantes_elements = []
                while stack and stack[-1] != '(':
                    parantes_elements.append(stack.pop())
                stack.pop()

                operators = [op for op in parantes_elements if op in ['+', '|', '-']]
                elements = [el for el in parantes_elements if el not in ['+', '|', '-']]
                if '|' in operators and ('+' in operators or '-' in operators):
                    raise ValueError(f"Mixed or missing operators in block: {operators}")
                if len(operators) == 0 and len(elements)!=1:
                    raise ValueError(f"Mixed or missing operators in block: {operators}")

                try:
                    operator = operators[0]
                    combined_query = QueryGenerator.build_bool_query(reversed(elements), operator)
                except:
                    if isinstance(parantes_elements[0], str):
                        combined_query = {"match_phrase": {"MESSAGE": elements[0]}}
                        # combined_query = {'should': {"match_phrase": {"MESSAGE": elements[0]}}}
                    else:
                        combined_query = elements

                if stack and stack[-1] == '-':
                    stack.pop()
                    if stack and stack[-1] != '+':
                        stack.append('+')
                    stack.append({"bool": {"must_not": [combined_query]}})
                else:
                    stack.append(combined_query)
            else:
                stack.append(token)

        while len(stack) > 1:
            parantes_elements = []
            while stack:
                parantes_elements.append(stack.pop())
            # stack.pop()

            operators = [op for op in parantes_elements if op in ['+', '|', '-']]
            if '|' in operators and ('+' in operators or '-' in operators):
                raise ValueError(f"Mixed or missing operators in block: {operators}")

            operator = operators[0]
            elements = [el for el in parantes_elements if el not in ['+', '|', '-']]

            combined_query = QueryGenerator.build_bool_query(reversed(elements), operator)

            if stack and stack[-1] == '-':
                stack.pop()
                if stack and stack[-1] != '+':
                    stack.append('+')
                stack.append({"bool": {"must_not": [combined_query]}})
            else:
                stack.append(combined_query)

        return stack[0] if stack else {}
