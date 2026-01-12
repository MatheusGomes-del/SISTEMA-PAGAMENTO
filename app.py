from flask import Flask, jsonify, request, send_file, render_template
from respository.database import db
from models.payments import Payment
from datetime import datetime, timedelta
from payments.pix import Pix

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'SECRET_KEY_WEBSOCKET'

db.init_app(app)

@app.route("/payments/pix", methods=["POST"])
def create_payment_pix():
    data = request.get_json()
    
    if 'value' not in data:
        return jsonify({"message": "Invalid value"}), 400
    
    expiration_date = datetime.now() + timedelta(minutes=30)

    new_payment = Payment(value=data['value'], expiration_date=expiration_date)

    pix_obj = Pix()
    data_payment_pix = pix_obj.create_payment()
    new_payment.bank_payment_id = data_payment_pix["bank_payment_id"]
    new_payment.qr_code = data_payment_pix["qr_code_path"]

    db.session.add(new_payment)
    db.session.commit()

    return jsonify({"message": "Pagamento foi criado",
                     "payment": new_payment.to_dict()})



@app.route('/payments/pix/qr_code/<file_name>', methods=['GET'])
def get_image(file_name):
    return send_file(f"static/img/{file_name}.png", mimetype='image/png')



@app.route('/payments/pix/confirmation', methods=["POST"])
def  pix_confimation():
    data = request.get_json()

    if "bank_payment_id" not in data or "value" not in data:
        return jsonify({"message": "Invalid payment data"}), 400
     
    payment = Payment.query.filter_by(bank_payment_id=data.get("bank_payment_id")).first()
    print(payment.value)

    if not payment or payment.paid:
        return jsonify({"message": "Payment not found"}), 404

    if float(data.get("value")) != payment.value:
        return jsonify({"message": "Invalid payment data"}), 400

    payment.paid = True
    db.session.commit()


    return jsonify({"message": "O pagamento foi confirmado"})


@app.route('/payments/pix/<int:payment_id>', methods=['GET'])
def payment_pix_page(payment_id):
    payment = Payment.query.get(payment_id)

    return render_template('payment.html', 
                           payment_id=payment_id,
                           value=payment.value,
                           host="http://127.0.0.1:5000",
                           qr_code=payment.qr_code)



@app.route('/payments/clear', methods=['DELETE'])
def clear_payments():
    Payment.query.delete()
    db.session.commit()
    return jsonify({"message": "Todos os pagamentos foram removidos"})

if __name__ == '__main__':
    app.run(debug=True)