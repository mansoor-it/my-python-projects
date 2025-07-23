from http.server import BaseHTTPRequestHandler, HTTPServer
import sqlite3
import json
import urllib.parse

class RequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write("<html><body><h1>مرحبًا في خادمكم!</h1></body></html>")
        elif self.path.startswith('/products'):
            self.handle_products()
        elif self.path.startswith('/cart'):
            self.handle_cart()
        elif self.path.startswith('/orders'):
            self.handle_orders()
        elif self.path.startswith('/users'):
            self.handle_users()
        else:
            self.send_response(404)
            self.end_headers()

    def handle_employees(self):
        # معالجة الطلبات الخاصة بالموظفين هنا
        pass

    def handle_products(self):
        conn = sqlite3.connect('ecommerce.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM products')
        products = cursor.fetchall()

        products_data = [{"id": p[0], "name": p[1], "price": p[2], "description": p[3], "quantity": p[4]} for p in products]

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(products_data).encode('utf-8'))
        conn.close()

    def handle_cart(self):
        # معالجة الطلبات الخاصة بالسلة هنا
        pass

    def handle_orders(self):
        # معالجة الطلبات الخاصة بالطلبات هنا
        pass

    def handle_users(self):
        # معالجة الطلبات الخاصة بالمستخدمين هنا
        pass

def run(server_class=HTTPServer, handler_class=RequestHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    print(f'Access it at: http://127.0.0.1:{port}/')  # عرض الرابط في التيرمينال
    httpd.serve_forever()

if __name__ == '__main__':
    run()