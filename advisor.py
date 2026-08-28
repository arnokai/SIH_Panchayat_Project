import yaml


def load_rules():
    with open("rules.yaml", "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    return data["rules"]


def get_advisory(rain_mm, tmax_c, crop="paddy", stage=None):

    rules = load_rules()
    advisories = []

    for rule in rules:

        # Check crop
        if "all" not in rule["crop"] and crop not in rule["crop"]:
            continue

        # Check stage if the rule has one
        if "stage" in rule:
            if stage not in rule["stage"]:
                continue

        # Values available to the rule condition
        condition = rule["condition"]

        try:
            if eval(condition, {
                "__builtins__": {}
            }, {
                "rain_mm": rain_mm,
                "tmax_c": tmax_c
            }):
                advisories.append({
                    "id": rule["id"],
                    "priority": rule["priority"],
                    "type": rule["type"],
                    "text_en": rule["text_en"],
                    "text_bn": rule["text_bn"]
                })

        except Exception as e:
            print(f"Rule error in {rule['id']}: {e}")

    return advisories


# Test
if __name__ == "__main__":

    rain = 25
    temperature = 34

    result = get_advisory(
        rain_mm=rain,
        tmax_c=temperature,
        crop="paddy"
    )

    print("\nADVISORY")
    print("-" * 40)

    for advisory in result:
        print("English:", advisory["text_en"])
        print("Bengali:", advisory["text_bn"])
        print("Priority:", advisory["priority"])
        