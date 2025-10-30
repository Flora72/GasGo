# GasGo
LPG Delivery made easy 

GasGo is a smart LPG access and delivery platform that connects households, vendors, and riders through a centralized system. It was born out of a personal frustration shared by many households in Kenya: the struggle to find safe, reliable cooking gas.

Many families have experienced the stress of chasing down vendors, only to receive half-filled cylinders or ones with defects. Beyond being a waste of money, this is a serious safety hazard. There have been heartbreaking cases of gas explosions caused by illegally refilled cylinders—lives lost, homes destroyed, trust broken.

GasGo is a response to that broken system. It’s about restoring safety, transparency, and dignity to something as essential as cooking fuel.

## Features

GasGo supports both smartphones and feature phones via USSD, making it accessible to a wide range of users. The platform enables:

- Customers to place gas orders and receive real-time delivery updates
- Vendors to verify their listings, manage inventory, and fulfill orders
- Riders to optimize delivery routes and trigger emergency alerts
- Admins to monitor platform activity and send SMS notifications

## Technology Stack

| Layer       | Technologies                                                                 |
|-------------|-------------------------------------------------------------------------------|
| Frontend    | HTML, CSS, JavaScript (mobile-first responsive design)                       |
| Backend     | Django (Python)                                                              |
| Database    | PostgreSQL                                                                   |
| APIs        | Africa’s Talking (SMS, USSD), Google Maps (routing), M-Pesa (payments)       |
| Deployment  | Render                                                                       |


## Getting Started

### **1. Clone the repository**

```bash
git clone https://github.com/Flora72/GasGo.git
cd gasgo
```
### **2. Create and activate a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```
### **3. Install dependencies**
```bash
pip install -r requirements.txt
```
### **4. Set up environment variables in a .env file**
```bash
env
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=127.0.0.1,localhost
```
Run migrations and start the server
```bash
python manage.py migrate
python manage.py runserver
```

## Contributing
GasGo is built with a mission to improve safety and access to clean energy.All contributions are welcome, especially from developers, designers, and community advocates passionate about social impact.

## License

This project is licensed under the MIT License.
