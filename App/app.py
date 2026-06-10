import pandas as pd

from flask import Flask, render_template, request

app = Flask(__name__)
dishes = 'dishes.csv'
df = pd.read_csv(dishes)
df.columns = df.columns.str.strip().str.lower()
NON_ALLERGEN_COLUMNS = ['dish', 'category']
for col in df.columns:
    if col not in NON_ALLERGEN_COLUMNS:

        df[col] = (
            df[col]
            .astype(str)
            .str.strip()
            .str.lower()
            .map({
                "true": True,
                "false": False,
                "1": True,
                "0": False,
                "yes": True,
                "no": False
            })
            .fillna(False)
        )
def find_alternative(current_row, selected_allergens):

    current_category = current_row['category']

    possible_alts = df[df['category'] == current_category]

    for _, alt in possible_alts.iterrows():

        safe = True

        for allergen in selected_allergens:

            if allergen in df.columns and alt[allergen] == True:
                safe = False
                break

        # don't recommend same dish
        if safe and alt['dish'] != current_row['dish']:
            return alt['dish']

    return None

@app.route('/', methods=['GET', 'POST'])
def index():

    allergens = [col for col in df.columns if col not in NON_ALLERGEN_COLUMNS]

    safe_results = []

    MODIFIABLE_DISHES = {"pizza"}

    SUBSTITUTIONS = {
        "gluten": "use gluten-free dough",
        "pork": "remove pork",
        "beef": "remove beef",
        "poultry": "remove poultry"
    }

    if request.method == 'POST' :

        selected_allergens = [a.lower() for a in request.form.getlist('request')]

        for _, row in df.iterrows():

            dish_name = str(row['dish']).lower()
            is_modifiable = dish_name in MODIFIABLE_DISHES

            is_safe = True
            modifications = []

            for allergen in selected_allergens:

                if allergen in df.columns and row[allergen] == True:

                    # ❌ cannot modify → reject dish
                    if not is_modifiable:

                        alternative = find_alternative(row, selected_allergens)

                        if alternative:
                            safe_results.append({
                                "dish": row['dish'],
                                "unsafe": True,
                                "alternative": alternative
                            })

                            is_safe = False
                            break


                    # ⚠ can modify → add substitution
                    if allergen in SUBSTITUTIONS:
                        modifications.append(SUBSTITUTIONS[allergen])

            if is_safe:
                safe_results.append({
                    "dish": row['dish'],
                    "modified": len(modifications) > 0,
                    "modifications": modifications
                })

        return render_template('results.html', results=safe_results)

    return render_template('index.html', allergens=allergens)

