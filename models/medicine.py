from extensions import db

class Medicine(db.Model):
    __tablename__ = 'medicines'
    medicine_id = db.Column(db.Integer, primary_key=True)
    medicine_name = db.Column(db.String(255), nullable=False)
    generic_name = db.Column(db.String(255))
    brand = db.Column(db.String(255))
    strength = db.Column(db.String(100))
    dosage_form = db.Column(db.String(100))
    manufacturer = db.Column(db.String(255))
    side_effects = db.Column(db.Text)
    contraindications = db.Column(db.Text)
    storage = db.Column(db.String(255))
    food_interaction = db.Column(db.Text)
    drug_interaction = db.Column(db.Text)
    warnings = db.Column(db.Text)

    def to_dict(self):
        return {
            'medicine_id': self.medicine_id,
            'medicine_name': self.medicine_name,
            'generic_name': self.generic_name,
            'brand': self.brand,
            'strength': self.strength,
            'dosage_form': self.dosage_form,
            'manufacturer': self.manufacturer
        }
