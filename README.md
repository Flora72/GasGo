# GasGo
LPG Delivery made easy 

GasGo is a smart LPG access and delivery platform that connects households, vendors, and riders through a centralized system. It was born out of a personal frustration shared by many households in Kenya: the struggle to find safe, reliable cooking gas.

Many families have experienced the stress of chasing down vendors, only to receive half-filled cylinders or ones with defects. Beyond being a waste of money, this is a serious safety hazard. There have been heartbreaking cases of gas explosions caused by illegally refilled cylinders—lives lost, homes destroyed, trust broken.

GasGo is a response to that broken system. It’s about restoring safety, transparency, and dignity to something as essential as cooking fuel.

## Features

GasGo supports both smartphones and laptops, making it accessible to a wide range of users. The platform enables:

- Customers to place gas orders
- Customers can track their gas orders 
- Customers can pay through mpesa
- Admins to monitor platform activity and send SMS notifications

## Technology Stack

| Layer       | Technologies                                                                 |
|-------------|-------------------------------------------------------------------------------|
| Frontend    | HTML, CSS, JavaScript (mobile-first responsive design)                       |
| Backend     | Django (Python)                                                              |
| Database    | PostgreSQL                                                                   |
| APIs        | Africa’s Talking (SMS, USSD), Google Maps (routing), M-Pesa (payments)       |
| Deployment  | Render                                                                       |

## Live Demo
You can access the live GasGo platform here: [https://gasgo-uby8.onrender.com/](https://gasgo-uby8.onrender.com/)

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

## Future Advancements
- Integration with licensed cylinder verification systems to detect illegal refills
- Transform the GasGo web app into a dedicated mobile app for Android and iOS.
- Loyalty and rewards system for repeat customers and trusted vendors
- Expanded USSD support for multilingual access across Kenya
- Rider performance analytics and delivery heatmaps
- Vendor onboarding dashboard with KYC verification
- Emergency response integration with local authorities

## Contributing
GasGo is built with a mission to improve safety and access to clean energy.All contributions are welcome, especially from developers, designers, and community advocates passionate about social impact.

## License

This project is licensed under the MIT License.
