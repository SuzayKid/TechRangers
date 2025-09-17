from dss.database import fetch_eligibility_rules, fetch_village_dss_data

class RuleEngine:
    def __init__(self):
        self.rules = self._load_rules()

    def _load_rules(self):
        """Loads eligibility rules from the database."""
        return fetch_eligibility_rules()

    def evaluate(self, scheme_name, data):
        """
        Evaluates eligibility for a given scheme against provided data.
        Data is expected to be a dictionary (e.g., a row from village_dss_data).
        """
        scheme_rules = [rule for rule in self.rules if rule['scheme_name'] == scheme_name]
        
        if not scheme_rules:
            return False, "No rules defined for this scheme."

        justifications = []
        all_conditions_met = True

        for rule in scheme_rules:
            attribute = rule['attribute']
            operator = rule['operator']
            value = rule['value']

            data_value = data.get(attribute)

            if data_value is None:
                all_conditions_met = False
                justifications.append(f"Missing data for attribute: {attribute}")
                continue

            condition_met = False
            try:
                if operator == '=':
                    condition_met = (str(data_value) == value)
                elif operator == '>':
                    condition_met = (float(data_value) > float(value))
                elif operator == '<':
                    condition_met = (float(data_value) < float(value))
                elif operator == '>=':
                    condition_met = (float(data_value) >= float(value))
                elif operator == '<=':
                    condition_met = (float(data_value) <= float(value))
                elif operator == 'LIKE':
                    condition_met = (value.lower() in str(data_value).lower())
                else:
                    justifications.append(f"Unsupported operator: {operator}")
                    all_conditions_met = False
                    continue
            except ValueError:
                justifications.append(f"Type conversion error for attribute {attribute} with value {data_value} and rule value {value}")
                all_conditions_met = False
                continue

            if not condition_met:
                all_conditions_met = False
                justifications.append(f"Condition not met: {attribute} {operator} {value} (actual: {data_value})")
        
        return all_conditions_met, justifications


class DSSEngine:
    def __init__(self):
        self.rule_engine = RuleEngine()
        # Define schemes and their priorities/descriptions
        self.schemes_info = {
            "PM-KISAN": {"priority": 1, "description": "Provides income support to all eligible farmer families."},
            "Jal Jeevan Mission": {"priority": 2, "description": "Aims to provide safe and adequate drinking water through individual household tap connections."},
            "MGNREGA": {"priority": 3, "description": "Guarantees the 'right to work' and aims to enhance livelihood security in rural areas."},
            "DAJGUA": {"priority": 4, "description": "Scheme for tribal welfare and development."}
            # Add other schemes as needed
        }

    def get_recommendations(self, input_type, input_id):
        """
        Generates scheme recommendations based on input_type and input_id.
        """
        dss_data = None
        if input_type == "village":
            dss_data = fetch_village_dss_data(village_id=input_id)
        elif input_type == "patta_holder":
            # TODO: Implement patta_holder to village mapping or direct patta_holder data fetching
            # For now, we'll assume patta_holder_id maps to a village_id for DSS data.
            # This needs to be refined based on actual patta_holder data availability.
            print("Warning: Patta holder logic is a placeholder. Assuming direct village data for now.")
            dss_data = fetch_village_dss_data(village_id=input_id) # Placeholder
        else:
            return {"error": "Invalid input type. Must be 'village' or 'patta_holder'."}

        if not dss_data:
            return {"error": f"No DSS data found for {input_type} ID {input_id}."}

        recommendations = []
        for scheme_name, info in self.schemes_info.items():
            is_eligible, justifications = self.rule_engine.evaluate(scheme_name, dss_data)
            if is_eligible:
                recommendations.append({
                    "scheme_name": scheme_name,
                    "description": info["description"],
                    "priority": info["priority"],
                    "justifications": justifications
                })
        
        # Sort recommendations by priority
        recommendations.sort(key=lambda x: x["priority"])

        return {"recommendations": recommendations, "dss_data_used": dict(dss_data)}
