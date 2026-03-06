<?php
/**
 * Monolithic E-Commerce Application
 * All business domains tightly coupled in a single PHP application
 * Using MySQL shared database
 */

// Suppress PHP errors from mixing with JSON responses
error_reporting(E_ALL);
ini_set('display_errors', '0');
ini_set('log_errors', '1');

// Database connection
function get_db() {
    $host = getenv('DB_HOST') ?: 'mysql';
    $dbname = getenv('DB_NAME') ?: 'ecommerce';
    $user = getenv('DB_USER') ?: 'ecommerce_user';
    $pass = getenv('DB_PASS') ?: 'ecommerce_pass';
    
    try {
        $pdo = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8mb4", $user, $pass);
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        return $pdo;
    } catch (PDOException $e) {
        die("Database connection failed: " . $e->getMessage());
    }
}

// Initialize database
function init_db($db) {
    $db->exec('CREATE TABLE IF NOT EXISTS orders (
        id VARCHAR(50) PRIMARY KEY,
        customer_id VARCHAR(50) NOT NULL,
        customer_name VARCHAR(255) NOT NULL,
        customer_email VARCHAR(255) NOT NULL,
        status VARCHAR(50) NOT NULL,
        total_amount DECIMAL(10,2) NOT NULL,
        warehouse_id VARCHAR(50),
        tracking_number VARCHAR(100),
        carrier VARCHAR(50),
        shipping_address TEXT,
        notes TEXT,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL,
        INDEX idx_customer (customer_id),
        INDEX idx_status (status)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4');
    
    $db->exec('CREATE TABLE IF NOT EXISTS order_items (
        id VARCHAR(50) PRIMARY KEY,
        order_id VARCHAR(50) NOT NULL,
        product_id VARCHAR(50) NOT NULL,
        product_name VARCHAR(255) NOT NULL,
        quantity INT NOT NULL,
        price DECIMAL(10,2) NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        INDEX idx_order (order_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4');
    
    $db->exec('CREATE TABLE IF NOT EXISTS inventory (
        product_id VARCHAR(50) PRIMARY KEY,
        product_name VARCHAR(255) NOT NULL,
        description TEXT,
        price DECIMAL(10,2) NOT NULL,
        stock_quantity INT NOT NULL,
        category VARCHAR(100),
        image_url VARCHAR(255),
        warehouse_location VARCHAR(100) DEFAULT "Aisle 3-B",
        weight_lbs DECIMAL(10,2) DEFAULT 1.5,
        dimensions VARCHAR(50) DEFAULT "12x8x6"
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4');
    
    $db->exec('CREATE TABLE IF NOT EXISTS payments (
        id VARCHAR(50) PRIMARY KEY,
        order_id VARCHAR(50) NOT NULL,
        amount DECIMAL(10,2) NOT NULL,
        payment_method VARCHAR(50) NOT NULL,
        status VARCHAR(50) NOT NULL,
        transaction_date DATETIME NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4');
    
    $db->exec('CREATE TABLE IF NOT EXISTS returns (
        id VARCHAR(50) PRIMARY KEY,
        order_id VARCHAR(50) NOT NULL,
        reason TEXT NOT NULL,
        status VARCHAR(50) NOT NULL,
        refund_amount DECIMAL(10,2),
        created_at DATETIME NOT NULL,
        processed_at DATETIME,
        FOREIGN KEY (order_id) REFERENCES orders(id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4');
    
    $db->exec('CREATE TABLE IF NOT EXISTS interactions (
        id VARCHAR(50) PRIMARY KEY,
        customer_id VARCHAR(50) NOT NULL,
        order_id VARCHAR(50),
        interaction_type VARCHAR(50) NOT NULL,
        notes TEXT,
        sentiment VARCHAR(50),
        created_at DATETIME NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4');
    
    $db->exec('CREATE TABLE IF NOT EXISTS order_status_history (
        id VARCHAR(50) PRIMARY KEY,
        order_id VARCHAR(50) NOT NULL,
        status VARCHAR(50) NOT NULL,
        notes TEXT,
        changed_by VARCHAR(100),
        created_at DATETIME NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        INDEX idx_order (order_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4');
    
    $db->exec('CREATE TABLE IF NOT EXISTS warehouses (
        id VARCHAR(50) PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        location VARCHAR(255) NOT NULL,
        capacity INT NOT NULL,
        current_load INT DEFAULT 0
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4');
    
    $db->exec('CREATE TABLE IF NOT EXISTS users (
        id VARCHAR(50) PRIMARY KEY,
        username VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        role VARCHAR(50) NOT NULL,
        created_at DATETIME NOT NULL,
        INDEX idx_username (username),
        INDEX idx_email (email)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4');
    
    // Add warehouse_location column if it doesn't exist (for existing databases)
    try {
        $db->exec('ALTER TABLE inventory ADD COLUMN warehouse_location VARCHAR(100) DEFAULT "Aisle 3-B"');
    } catch (PDOException $e) {
        // Column already exists, ignore error
    }
    
    // Add weight_lbs column if it doesn't exist
    try {
        $db->exec('ALTER TABLE inventory ADD COLUMN weight_lbs DECIMAL(10,2) DEFAULT 1.5');
    } catch (PDOException $e) {
        // Column already exists, ignore error
    }
    
    // Add dimensions column if it doesn't exist
    try {
        $db->exec('ALTER TABLE inventory ADD COLUMN dimensions VARCHAR(50) DEFAULT "12x8x6"');
    } catch (PDOException $e) {
        // Column already exists, ignore error
    }
}

// Seed sample data
function seed_data($db) {
    // Check and seed users first (critical for login)
    $stmt = $db->query('SELECT COUNT(*) as count FROM users');
    $row = $stmt->fetch(PDO::FETCH_ASSOC);
    if ($row['count'] == 0) {
        $users = [
            ['cust-001', 'customer', password_hash('customer123', PASSWORD_BCRYPT), 'John Doe', 'john.doe@example.com', 'customer', date('Y-m-d H:i:s')],
            ['admin-001', 'admin', password_hash('admin123', PASSWORD_BCRYPT), 'Admin User', 'admin@example.com', 'admin', date('Y-m-d H:i:s')],
        ];
        
        $stmt = $db->prepare('INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)');
        foreach ($users as $user) {
            $stmt->execute($user);
        }
    }
    
    // Check and seed inventory
    $stmt = $db->query('SELECT COUNT(*) as count FROM inventory');
    $row = $stmt->fetch(PDO::FETCH_ASSOC);
    if ($row['count'] == 0) {
        $products = [
            ['prod-001', 'Classic T-Shirt', 'Comfortable cotton t-shirt', 29.99, 100, 'Clothing', '/images/tshirt.jpg'],
            ['prod-002', 'Denim Jeans', 'Classic fit denim jeans', 79.99, 50, 'Clothing', '/images/jeans.jpg'],
            ['prod-003', 'Running Shoes', 'Lightweight running shoes', 89.99, 75, 'Footwear', '/images/shoes.jpg'],
            ['prod-004', 'Backpack', 'Durable travel backpack', 49.99, 30, 'Accessories', '/images/backpack.jpg'],
            ['prod-005', 'Hoodie', 'Warm fleece hoodie', 59.99, 60, 'Clothing', '/images/hoodie.jpg'],
        ];
        
        $stmt = $db->prepare('INSERT INTO inventory VALUES (?, ?, ?, ?, ?, ?, ?)');
        foreach ($products as $product) {
            $stmt->execute($product);
        }
    }
    
    // Check and seed warehouses
    $stmt = $db->query('SELECT COUNT(*) as count FROM warehouses');
    $row = $stmt->fetch(PDO::FETCH_ASSOC);
    if ($row['count'] == 0) {
        $warehouses = [
            ['wh-001', 'Seattle Warehouse', 'Seattle, WA', 10000, 0],
            ['wh-002', 'Portland Warehouse', 'Portland, OR', 8000, 0],
            ['wh-003', 'San Francisco Warehouse', 'San Francisco, CA', 12000, 0],
        ];
        
        $stmt = $db->prepare('INSERT INTO warehouses VALUES (?, ?, ?, ?, ?)');
        foreach ($warehouses as $warehouse) {
            $stmt->execute($warehouse);
        }
    }
    
    // Check and seed sample order
    $stmt = $db->query('SELECT COUNT(*) as count FROM orders');
    $row = $stmt->fetch(PDO::FETCH_ASSOC);
    if ($row['count'] == 0) {
        $order_id = uniqid('order-');
        $created_at = date('Y-m-d H:i:s', strtotime('-5 days'));
        $updated_at = date('Y-m-d H:i:s', strtotime('-2 days'));
        
        $stmt = $db->prepare('INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)');
        $stmt->execute([$order_id, 'cust-001', 'John Doe', 'john.doe@example.com', 'delivered', 109.98, 'wh-001', 'TRACK123456', 'UPS', '123 Main St, Seattle, WA 98101', null, $created_at, $updated_at]);
        
        $stmt = $db->prepare('INSERT INTO order_items VALUES (?, ?, ?, ?, ?, ?)');
        $stmt->execute([uniqid('item-'), $order_id, 'prod-001', 'Classic T-Shirt', 2, 29.99]);
        
        $stmt = $db->prepare('INSERT INTO payments VALUES (?, ?, ?, ?, ?, ?)');
        $stmt->execute([uniqid('pay-'), $order_id, 109.98, 'credit_card', 'completed', $created_at]);
    }
}

// Simple session management
session_start();

$db = get_db();
init_db($db);
seed_data($db);

// Set current user from session (needed for API endpoints)
$current_user = $_SESSION['user'] ?? null;

// Helper function to update order status and log history
function update_order_status($db, $order_id, $new_status, $notes = '', $changed_by = 'system') {
    $stmt = $db->prepare('UPDATE orders SET status = ?, updated_at = ? WHERE id = ?');
    $stmt->execute([$new_status, date('Y-m-d H:i:s'), $order_id]);
    
    $stmt = $db->prepare('INSERT INTO order_status_history VALUES (?, ?, ?, ?, ?, ?)');
    $stmt->execute([uniqid('hist-'), $order_id, $new_status, $notes, $changed_by, date('Y-m-d H:i:s')]);
}

$request_uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$request_method = $_SERVER['REQUEST_METHOD'];

// Handle logout
if ($request_uri === '/logout') {
    session_destroy();
    header('Location: /');
    exit;
}

// Handle login
if ($request_uri === '/login' && $request_method === 'POST') {
    $username = $_POST['username'] ?? '';
    $password = $_POST['password'] ?? '';
    
    // Query users from database
    $stmt = $db->prepare('SELECT * FROM users WHERE username = ?');
    $stmt->execute([$username]);
    $user = $stmt->fetch(PDO::FETCH_ASSOC);
    
    if ($user && password_verify($password, $user['password'])) {
        unset($user['password']); // Don't store password in session
        $_SESSION['user'] = $user;
        header('Location: /');
        exit;
    } else {
        $_SESSION['login_error'] = 'Invalid username or password';
        header('Location: /');
        exit;
    }
}

$request_uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$request_method = $_SERVER['REQUEST_METHOD'];

// API Routes
if (strpos($request_uri, '/api/') === 0) {
    header('Content-Type: application/json');
    
    // Check authentication for API calls
    if (!isset($_SESSION['user'])) {
        http_response_code(401);
        echo json_encode(['error' => 'Unauthorized']);
        exit;
    }
    
    if ($request_uri === '/api/products' && $request_method === 'GET') {
        $stmt = $db->query('SELECT * FROM inventory');
        $products = $stmt->fetchAll(PDO::FETCH_ASSOC);
        echo json_encode(['products' => $products]);
        exit;
    }

    
    if ($request_uri === '/api/orders' && $request_method === 'POST') {
        $data = json_decode(file_get_contents('php://input'), true);
        $db->beginTransaction();
        try {
            $order_id = uniqid('order-');
            $total_amount = 0;
            
            // Use logged-in customer info
            $customer_id = $_SESSION['user']['id'];
            $customer_name = $_SESSION['user']['name'];
            $customer_email = $_SESSION['user']['email'];
            $shipping_address = $data['shipping_address'] ?? null;
            
            foreach ($data['items'] as $item) {
                $stmt = $db->prepare('SELECT stock_quantity, price FROM inventory WHERE product_id = ?');
                $stmt->execute([$item['product_id']]);
                $product = $stmt->fetch(PDO::FETCH_ASSOC);
                if (!$product || $product['stock_quantity'] < $item['quantity']) {
                    throw new Exception('Insufficient inventory');
                }
                $total_amount += $product['price'] * $item['quantity'];
            }
            
            $stmt = $db->prepare('INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)');
            $stmt->execute([$order_id, $customer_id, $customer_name, $customer_email, 
                'pending', $total_amount, null, null, null, $shipping_address, null, date('Y-m-d H:i:s'), date('Y-m-d H:i:s')]);
            
            foreach ($data['items'] as $item) {
                $stmt = $db->prepare('SELECT product_name, price FROM inventory WHERE product_id = ?');
                $stmt->execute([$item['product_id']]);
                $product = $stmt->fetch(PDO::FETCH_ASSOC);
                
                $stmt = $db->prepare('INSERT INTO order_items VALUES (?, ?, ?, ?, ?, ?)');
                $stmt->execute([uniqid('item-'), $order_id, $item['product_id'], 
                    $product['product_name'], $item['quantity'], $product['price']]);
                
                $stmt = $db->prepare('UPDATE inventory SET stock_quantity = stock_quantity - ? WHERE product_id = ?');
                $stmt->execute([$item['quantity'], $item['product_id']]);
            }
            
            $stmt = $db->prepare('INSERT INTO payments VALUES (?, ?, ?, ?, ?, ?)');
            $stmt->execute([uniqid('pay-'), $order_id, $total_amount, 
                $data['payment_method'] ?? 'credit_card', 'completed', date('Y-m-d H:i:s')]);
            
            update_order_status($db, $order_id, 'confirmed', 'Order confirmed and payment processed', 'system');
            
            $db->commit();
            echo json_encode(['success' => true, 'order_id' => $order_id, 'total_amount' => $total_amount]);
        } catch (Exception $e) {
            $db->rollBack();
            http_response_code(400);
            echo json_encode(['error' => $e->getMessage()]);
        }
        exit;
    }

    
    // ========== DECISION-MAKING ENDPOINTS ==========
    // These endpoints provide rich context data for manual decision-making
    
    // Route: GET /api/orders/{orderId}/validation-data - Get fraud/validation context
    if (preg_match('#^/api/orders/([^/]+)/validation-data$#', $request_uri, $matches) && $request_method === 'GET') {
        $order_id = $matches[1];
        
        try {
            // Get order details
            $stmt = $db->prepare('SELECT * FROM orders WHERE id = ?');
            $stmt->execute([$order_id]);
            $order = $stmt->fetch(PDO::FETCH_ASSOC);
            
            if (!$order) {
                http_response_code(404);
                echo json_encode(['error' => 'Order not found']);
                exit;
            }
            
            // Get customer history
            $stmt = $db->prepare('SELECT MIN(created_at) as first_order, COUNT(*) as total_orders, SUM(total_amount) as total_spent, MAX(created_at) as last_order FROM orders WHERE customer_id = ?');
            $stmt->execute([$order['customer_id']]);
            $customer_stats = $stmt->fetch(PDO::FETCH_ASSOC);
            
            $account_age_days = $customer_stats['first_order'] ? 
                (int)((time() - strtotime($customer_stats['first_order'])) / 86400) : 0;
            
            $avg_order_value = $customer_stats['total_orders'] > 0 ? 
                $customer_stats['total_spent'] / $customer_stats['total_orders'] : 0;
            
            // Calculate risk factors
            $risk_factors = [];
            $fraud_score = 0;
            
            if ($account_age_days < 90) {
                $risk_factors[] = [
                    'factor' => 'New Customer',
                    'severity' => 'medium',
                    'description' => "Account created $account_age_days days ago"
                ];
                $fraud_score += 20;
            }
            
            if ($order['total_amount'] > $avg_order_value * 1.5 && $customer_stats['total_orders'] > 0) {
                $pct_above = round((($order['total_amount'] / $avg_order_value) - 1) * 100);
                $risk_factors[] = [
                    'factor' => 'High Value Order',
                    'severity' => 'medium',
                    'description' => "Order value \${$order['total_amount']} is {$pct_above}% above customer average"
                ];
                $fraud_score += 15;
            }
            
            // Check if first order is high value
            if ($customer_stats['total_orders'] == 1 && $order['total_amount'] > 200) {
                $risk_factors[] = [
                    'factor' => 'First Order High Value',
                    'severity' => 'high',
                    'description' => "First order with value \${$order['total_amount']}"
                ];
                $fraud_score += 25;
            }
            
            // Address match (always low risk in our demo)
            $risk_factors[] = [
                'factor' => 'Address Match',
                'severity' => 'low',
                'description' => 'Shipping and billing addresses match'
            ];
            
            $recommendation = $fraud_score > 40 ? 'Manual review recommended' : 
                             ($fraud_score > 20 ? 'Low risk - quick review suggested' : 'Low risk - auto-approve candidate');
            
            echo json_encode([
                'order' => [
                    'id' => $order['id'],
                    'total' => (float)$order['total_amount'],
                    'shipping_address' => $order['shipping_address'] ?: 'Not provided',
                    'billing_address' => 'Same as shipping'
                ],
                'customer' => [
                    'id' => $order['customer_id'],
                    'name' => $order['customer_name'],
                    'email' => $order['customer_email'],
                    'account_age_days' => $account_age_days,
                    'total_orders' => (int)$customer_stats['total_orders'],
                    'total_spent' => (float)$customer_stats['total_spent'],
                    'last_order_date' => $customer_stats['last_order']
                ],
                'risk_factors' => $risk_factors,
                'fraud_score' => $fraud_score,
                'recommendation' => $recommendation
            ]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['error' => $e->getMessage()]);
        }
        exit;
    }
    
    // Route: GET /api/warehouses/assignment-options - Get warehouse comparison data
    if (preg_match('#^/api/warehouses/assignment-options#', $request_uri) && $request_method === 'GET') {
        $order_id = $_GET['orderId'] ?? null;
        
        // Optional: Get warehouse load overrides from control panel
        $load_overrides = [];
        if (isset($_GET['warehouseLoads'])) {
            $load_overrides = json_decode($_GET['warehouseLoads'], true) ?: [];
        }
        
        if (!$order_id) {
            http_response_code(400);
            echo json_encode(['error' => 'orderId parameter required']);
            exit;
        }
        
        try {
            // Get order details
            $stmt = $db->prepare('SELECT * FROM orders WHERE id = ?');
            $stmt->execute([$order_id]);
            $order = $stmt->fetch(PDO::FETCH_ASSOC);
            
            if (!$order) {
                http_response_code(404);
                echo json_encode(['error' => 'Order not found']);
                exit;
            }
            
            // Parse customer address to get city and state
            $customer_city = 'Seattle';
            $customer_state = 'WA';
            if ($order['shipping_address']) {
                // Parse: "7103 Carver Ave, Austin, TX 78752"
                if (preg_match('/,\s*([^,]+),\s*([A-Z]{2})\s+\d{5}/', $order['shipping_address'], $matches)) {
                    $customer_city = trim($matches[1]);
                    $customer_state = $matches[2];
                }
            }
            
            // City coordinates (lat, lon) for distance calculation
            $city_coords = [
                'Seattle' => [47.6062, -122.3321],
                'Portland' => [45.5152, -122.6784],
                'San Francisco' => [37.7749, -122.4194],
                'Austin' => [30.2672, -97.7431],
                'Dallas' => [32.7767, -96.7970],
                'Houston' => [29.7604, -95.3698],
                'Phoenix' => [33.4484, -112.0740],
                'Denver' => [39.7392, -104.9903],
                'Los Angeles' => [34.0522, -118.2437],
                'San Diego' => [32.7157, -117.1611]
            ];
            
            $customer_coords = $city_coords[$customer_city] ?? $city_coords['Seattle'];
            
            // Warehouse coordinates
            $warehouse_coords = [
                'wh-001' => [47.6062, -122.3321], // Seattle
                'wh-002' => [45.5152, -122.6784], // Portland
                'wh-003' => [37.7749, -122.4194]  // San Francisco
            ];
            
            // Haversine formula to calculate distance
            function calculate_distance($lat1, $lon1, $lat2, $lon2) {
                $earth_radius = 3959; // miles
                $lat1_rad = deg2rad($lat1);
                $lat2_rad = deg2rad($lat2);
                $delta_lat = deg2rad($lat2 - $lat1);
                $delta_lon = deg2rad($lon2 - $lon1);
                
                $a = sin($delta_lat / 2) * sin($delta_lat / 2) +
                     cos($lat1_rad) * cos($lat2_rad) *
                     sin($delta_lon / 2) * sin($delta_lon / 2);
                $c = 2 * atan2(sqrt($a), sqrt(1 - $a));
                
                return $earth_radius * $c;
            }
            
            // Get all warehouses
            $stmt = $db->query('SELECT * FROM warehouses');
            $warehouses = $stmt->fetchAll(PDO::FETCH_ASSOC);
            
            $warehouse_options = [];
            foreach ($warehouses as $wh) {
                $wh_coords = $warehouse_coords[$wh['id']] ?? [47.6062, -122.3321];
                $distance = round(calculate_distance(
                    $customer_coords[0], $customer_coords[1],
                    $wh_coords[0], $wh_coords[1]
                ));
                
                $shipping_cost = 5.00 + ($distance * 0.05);
                $delivery_days = $distance < 100 ? 1 : ($distance < 500 ? 2 : ($distance < 1000 ? 3 : 4));
                
                // Apply load override from control panel if set
                $load_pct = ($wh['current_load'] / $wh['capacity']) * 100;
                if (isset($load_overrides[$wh['name']])) {
                    $load_pct = (float)$load_overrides[$wh['name']];
                }
                
                // Store for later scoring (we'll calculate relative scores after we have all distances)
                $temp_score_data = [
                    'distance' => $distance,
                    'load_pct' => $load_pct
                ];
                
                $carriers = ['UPS', 'FedEx', 'USPS'];
                if ($load_pct > 80) {
                    $carriers = ['UPS']; // Limited carriers when busy
                }
                
                $warehouse_options[] = [
                    'id' => $wh['id'],
                    'name' => $wh['name'],
                    'location' => $wh['location'],
                    'distance_miles' => $distance,
                    'shipping_cost' => round($shipping_cost, 2),
                    'estimated_delivery_days' => $delivery_days,
                    'current_load' => (int)$wh['current_load'],
                    'capacity' => (int)$wh['capacity'],
                    'load_percentage' => round($load_pct, 1),
                    'inventory_available' => true,
                    'carriers_available' => $carriers,
                    'weather_status' => $distance < 200 ? 'Clear' : 'Check regional conditions',
                    'recommendation_score' => 0, // Will calculate after we have all warehouses
                    '_score_data' => $temp_score_data
                ];
            }
            
            // Calculate relative recommendation scores
            if (count($warehouse_options) > 0) {
                // Find min/max distances for normalization
                $distances = array_column($warehouse_options, 'distance_miles');
                $min_distance = min($distances);
                $max_distance = max($distances);
                $distance_range = $max_distance - $min_distance;
                
                foreach ($warehouse_options as &$wh_opt) {
                    $score = 100;
                    
                    // Distance score (0-60 points): closer is better
                    if ($distance_range > 0) {
                        $distance_normalized = ($wh_opt['distance_miles'] - $min_distance) / $distance_range;
                        $score -= ($distance_normalized * 60); // Best gets 100, worst gets 40
                    }
                    
                    // Load score (0-30 points): less loaded is better
                    $score -= ($wh_opt['_score_data']['load_pct'] * 0.3);
                    
                    // Delivery time bonus (0-10 points): faster is better
                    $score += (5 - $wh_opt['estimated_delivery_days']) * 2.5;
                    
                    $wh_opt['recommendation_score'] = round(max(0, min(100, $score)), 1);
                    unset($wh_opt['_score_data']); // Remove temp data
                }
                unset($wh_opt); // Break reference
            }
            
            // Sort by recommendation score
            usort($warehouse_options, function($a, $b) {
                return $b['recommendation_score'] <=> $a['recommendation_score'];
            });
            
            echo json_encode([
                'order' => [
                    'id' => $order_id,
                    'shipping_address' => $order['shipping_address'] ?: 'Not specified',
                    'destination_lat' => $customer_coords[0],
                    'destination_lng' => $customer_coords[1]
                ],
                'warehouses' => $warehouse_options
            ]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['error' => $e->getMessage()]);
        }
        exit;
    }
    
    // Route: GET /api/orders/{orderId}/picking-details - Get picking context
    if (preg_match('#^/api/orders/([^/]+)/picking-details$#', $request_uri, $matches) && $request_method === 'GET') {
        $order_id = $matches[1];
        
        try {
            $stmt = $db->prepare('SELECT * FROM orders WHERE id = ?');
            $stmt->execute([$order_id]);
            $order = $stmt->fetch(PDO::FETCH_ASSOC);
            
            if (!$order) {
                http_response_code(404);
                echo json_encode(['error' => 'Order not found']);
                exit;
            }
            
            // Get order items with product details
            $stmt = $db->prepare('
                SELECT oi.*, i.warehouse_location 
                FROM order_items oi 
                LEFT JOIN inventory i ON oi.product_id = i.product_id 
                WHERE oi.order_id = ?
            ');
            $stmt->execute([$order_id]);
            $items = $stmt->fetchAll(PDO::FETCH_ASSOC);
            
            if (empty($items)) {
                http_response_code(404);
                echo json_encode(['error' => 'No items found for this order']);
                exit;
            }
            
            $picking_items = [];
            $total_time = 0;
            
            foreach ($items as $item) {
                $pick_time = 2 + ($item['quantity'] * 0.5);
                $total_time += $pick_time;
                
                $picking_items[] = [
                    'product_id' => $item['product_id'],
                    'name' => $item['product_name'],
                    'quantity' => (int)$item['quantity'],
                    'location' => $item['warehouse_location'] ?? 'Aisle 3-B',
                    'special_handling' => 'None',
                    'estimated_pick_time_minutes' => round($pick_time, 1)
                ];
            }
            
            // Mock picker data with realistic status - use AI control panel settings if available
            $picker_statuses = [
                'picker-001' => 'Available',
                'picker-002' => 'Available',
                'picker-003' => 'On Break'
            ];
            
            // Parse picker statuses from query parameters
            // PHP automatically parses pickerStatus[picker-001]=Available into $_GET['pickerStatus']['picker-001']
            if (isset($_GET['pickerStatus']) && is_array($_GET['pickerStatus'])) {
                foreach ($_GET['pickerStatus'] as $picker_id => $status) {
                    $picker_statuses[$picker_id] = $status;
                }
            }
            
            $pickers = [
                ['id' => 'picker-001', 'name' => 'Mike Johnson', 'current_location' => 'Aisle 2', 'efficiency_rating' => 4.8, 'orders_today' => 23, 'status' => $picker_statuses['picker-001']],
                ['id' => 'picker-002', 'name' => 'Sarah Chen', 'current_location' => 'Aisle 5', 'efficiency_rating' => 4.9, 'orders_today' => 19, 'status' => $picker_statuses['picker-002']],
                ['id' => 'picker-003', 'name' => 'David Martinez', 'current_location' => 'Aisle 1', 'efficiency_rating' => 4.7, 'orders_today' => 27, 'status' => $picker_statuses['picker-003']]
            ];
            
            echo json_encode([
                'order_id' => $order_id,
                'warehouse_id' => $order['warehouse_id'] ?? 'WH-001',
                'items' => $picking_items,
                'available_pickers' => $pickers,
                'total_estimated_time_minutes' => round($total_time + 3, 1),
                'complexity' => count($picking_items) > 3 ? 'Medium' : 'Low'
            ]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['error' => $e->getMessage()]);
        }
        exit;
    }
    
    // Route: GET /api/orders/{orderId}/packing-options - Get packing context
    if (preg_match('#^/api/orders/([^/]+)/packing-options$#', $request_uri, $matches) && $request_method === 'GET') {
        $order_id = $matches[1];
        
        try {
            // Get order items with dimensions
            $stmt = $db->prepare('
                SELECT oi.quantity, i.weight_lbs, i.dimensions 
                FROM order_items oi 
                JOIN inventory i ON oi.product_id = i.product_id 
                WHERE oi.order_id = ?
            ');
            $stmt->execute([$order_id]);
            $items = $stmt->fetchAll(PDO::FETCH_ASSOC);
            
            $total_weight = 0;
            $total_volume = 0;
            foreach ($items as $item) {
                $total_weight += $item['weight_lbs'] * $item['quantity'];
                // Simple volume calculation
                $total_volume += 100 * $item['quantity'];
            }
            
            // Box options
            $boxes = [
                ['id' => 'box-small', 'name' => 'Small Box (10x8x6)', 'volume' => 480, 'cost' => 0.45],
                ['id' => 'box-medium', 'name' => 'Medium Box (12x10x8)', 'volume' => 960, 'cost' => 0.65],
                ['id' => 'box-large', 'name' => 'Large Box (16x12x10)', 'volume' => 1920, 'cost' => 0.95]
            ];
            
            $box_options = [];
            foreach ($boxes as $box) {
                $fits = $total_volume <= $box['volume'];
                $waste_pct = $fits ? round((($box['volume'] - $total_volume) / $box['volume']) * 100) : 0;
                $recommended = $fits && $waste_pct < 30;
                
                $box_options[] = [
                    'id' => $box['id'],
                    'name' => $box['name'],
                    'cost' => $box['cost'],
                    'fits' => $fits,
                    'waste_percentage' => $waste_pct,
                    'recommended' => $recommended
                ];
            }
            
            // Add dimensions field to box options
            foreach ($box_options as &$box) {
                $box['dimensions'] = $box['name']; // Already includes dimensions in name
            }
            
            echo json_encode([
                'order' => [
                    'id' => $order_id,
                    'total_volume_cubic_inches' => round($total_volume),
                    'total_weight_lbs' => round($total_weight, 2),
                    'max_length' => 10,
                    'max_width' => 8,
                    'total_height' => 6
                ],
                'box_options' => $box_options
            ]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['error' => $e->getMessage()]);
        }
        exit;
    }
    
    // Route: GET /api/orders/{orderId}/quality-checklist - Get QC checklist
    if (preg_match('#^/api/orders/([^/]+)/quality-checklist$#', $request_uri, $matches) && $request_method === 'GET') {
        $order_id = $matches[1];
        
        // Get AI control panel settings
        $qc_strictness = $_GET['qcStrictness'] ?? 'standard';
        $qc_threshold = isset($_GET['qcThreshold']) ? (int)$_GET['qcThreshold'] : 100;
        
        try {
            $stmt = $db->prepare('SELECT * FROM orders WHERE id = ?');
            $stmt->execute([$order_id]);
            $order = $stmt->fetch(PDO::FETCH_ASSOC);
            
            if (!$order) {
                http_response_code(404);
                echo json_encode(['error' => 'Order not found']);
                exit;
            }
            
            // Get item count
            $stmt = $db->prepare('SELECT COUNT(*) as item_count FROM order_items WHERE order_id = ?');
            $stmt->execute([$order_id]);
            $item_count = $stmt->fetch(PDO::FETCH_ASSOC)['item_count'];
            
            // Base checklist
            $checklist = [
                ['id' => 'check-items', 'item' => 'Verify all items present', 'description' => 'Confirm all items listed in the order are included in the package', 'status' => 'pending', 'critical' => true],
                ['id' => 'check-quantity', 'item' => 'Verify quantities match order', 'description' => 'Check that the quantity of each item matches the order', 'status' => 'pending', 'critical' => true],
                ['id' => 'check-condition', 'item' => 'Inspect for damage/defects', 'description' => 'Examine items for any damage, defects, or quality issues', 'status' => 'pending', 'critical' => true],
                ['id' => 'check-packaging', 'item' => 'Verify proper packaging', 'description' => 'Ensure items are properly protected with appropriate materials', 'status' => 'pending', 'critical' => false],
                ['id' => 'check-label', 'item' => 'Verify shipping label accuracy', 'description' => 'Confirm shipping label has correct address and order information', 'status' => 'pending', 'critical' => true],
                ['id' => 'check-weight', 'item' => 'Weight verification', 'description' => 'Verify package weight matches expected weight', 'status' => 'pending', 'critical' => false]
            ];
            
            // Add extra checks based on strictness level
            if ($qc_strictness === 'high') {
                $checklist[] = ['id' => 'check-barcode', 'item' => 'Scan all barcodes', 'description' => 'Verify each item barcode matches order system', 'status' => 'pending', 'critical' => true];
                $checklist[] = ['id' => 'check-photos', 'item' => 'Take package photos', 'description' => 'Document package contents with photos', 'status' => 'pending', 'critical' => false];
            } elseif ($qc_strictness === 'expedited') {
                // Remove non-critical checks for expedited
                $checklist = array_filter($checklist, function($item) {
                    return $item['critical'];
                });
                $checklist = array_values($checklist); // Re-index array
            }
            
            echo json_encode([
                'order' => [
                    'id' => $order_id,
                    'customer_name' => $order['customer_name'],
                    'item_count' => $item_count
                ],
                'checklist' => $checklist,
                'qc_settings' => [
                    'strictness' => $qc_strictness,
                    'auto_pass_threshold' => $qc_threshold
                ]
            ]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['error' => $e->getMessage()]);
        }
        exit;
    }
    
    // Route: GET /api/carriers/shipping-options - Get carrier comparison
    if (preg_match('#^/api/carriers/shipping-options#', $request_uri) && $request_method === 'GET') {
        $order_id = $_GET['orderId'] ?? null;
        
        if (!$order_id) {
            http_response_code(400);
            echo json_encode(['error' => 'orderId parameter required']);
            exit;
        }
        
        // Get AI control panel settings
        $shipping_multiplier = isset($_GET['shippingMultiplier']) ? (float)$_GET['shippingMultiplier'] : 1.0;
        $carrier_reliability = $_GET['carrierReliability'] ?? 'normal';
        $shipping_priority = $_GET['shippingPriority'] ?? 'balanced';
        
        try {
            $stmt = $db->prepare('SELECT * FROM orders WHERE id = ?');
            $stmt->execute([$order_id]);
            $order = $stmt->fetch(PDO::FETCH_ASSOC);
            
            if (!$order) {
                http_response_code(404);
                echo json_encode(['error' => 'Order not found']);
                exit;
            }
            
            // Get total weight from order items
            $stmt = $db->prepare('
                SELECT SUM(oi.quantity * i.weight_lbs) as total_weight 
                FROM order_items oi 
                JOIN inventory i ON oi.product_id = i.product_id 
                WHERE oi.order_id = ?
            ');
            $stmt->execute([$order_id]);
            $result = $stmt->fetch(PDO::FETCH_ASSOC);
            $weight = round($result['total_weight'] ?? 2.0, 2);
            
            // Parse customer address to get state
            $customer_state = 'WA'; // Default
            if ($order['shipping_address'] && preg_match('/,\s*([A-Z]{2})\s+\d{5}/', $order['shipping_address'], $matches)) {
                $customer_state = $matches[1];
            }
            
            // Parse customer city for coordinate lookup
            $customer_city = '';
            if ($order['shipping_address'] && preg_match('/,\s*([^,]+),\s*[A-Z]{2}/', $order['shipping_address'], $matches)) {
                $customer_city = trim($matches[1]);
            }
            
            // Get warehouse location
            $stmt = $db->prepare('SELECT location FROM warehouses WHERE id = ?');
            $stmt->execute([$order['warehouse_id']]);
            $warehouse = $stmt->fetch(PDO::FETCH_ASSOC);
            $warehouse_location = $warehouse['location'] ?? 'Seattle, WA';
            
            // Parse warehouse city and state
            if (preg_match('/([^,]+),\s*([A-Z]{2})/', $warehouse_location, $matches)) {
                $warehouse_city = trim($matches[1]);
                $warehouse_state = $matches[2];
            } else {
                $warehouse_city = 'Seattle';
                $warehouse_state = 'WA';
            }
            
            // City coordinates for distance calculation
            $city_coords = [
                'Seattle' => [47.6062, -122.3321],
                'Portland' => [45.5152, -122.6784],
                'San Francisco' => [37.7749, -122.4194],
                'Austin' => [30.2672, -97.7431],
                'Dallas' => [32.7767, -96.7970],
                'Houston' => [29.7604, -95.3698],
                'Phoenix' => [33.4484, -112.0740],
                'Denver' => [39.7392, -104.9903],
                'Los Angeles' => [34.0522, -118.2437],
                'San Diego' => [32.7157, -117.1611]
            ];
            
            // Get coordinates
            $wh_coords = $city_coords[$warehouse_city] ?? [47.6062, -122.3321];
            $customer_coords = $city_coords[$customer_city] ?? [47.6062, -122.3321];
            
            // Calculate distance using Haversine formula
            $distance = round(3959 * acos(
                cos(deg2rad($customer_coords[0])) * 
                cos(deg2rad($wh_coords[0])) * 
                cos(deg2rad($wh_coords[1]) - deg2rad($customer_coords[1])) + 
                sin(deg2rad($customer_coords[0])) * 
                sin(deg2rad($wh_coords[0]))
            ));
            
            // Calculate dynamic shipping costs based on distance and weight
            $base_cost = 5.00;
            $distance_cost = $distance * 0.05;
            $weight_cost = $weight * 0.50;
            
            // Apply shipping multiplier from control panel
            $cost_multiplier = $shipping_multiplier;
            
            // Set reliability score based on control panel setting
            $reliability_map = [
                'normal' => 98,
                'high' => 95,
                'weather' => 90
            ];
            $base_reliability = $reliability_map[$carrier_reliability] ?? 98;
            
            $carriers = [
                [
                    'carrier' => 'UPS',
                    'services' => [
                        ['service' => 'Ground', 'multiplier' => 1.0, 'days' => $distance < 100 ? 1 : ($distance < 500 ? 2 : ($distance < 1000 ? 3 : 4)), 'insurance' => false],
                        ['service' => '2nd Day Air', 'multiplier' => 2.2, 'days' => 2, 'insurance' => true],
                        ['service' => 'Next Day Air', 'multiplier' => 3.8, 'days' => 1, 'insurance' => true]
                    ]
                ],
                [
                    'carrier' => 'FedEx',
                    'services' => [
                        ['service' => 'Ground', 'multiplier' => 1.1, 'days' => $distance < 100 ? 1 : ($distance < 500 ? 2 : ($distance < 1000 ? 3 : 4)), 'insurance' => false],
                        ['service' => 'Express Saver', 'multiplier' => 2.6, 'days' => 2, 'insurance' => true]
                    ]
                ],
                [
                    'carrier' => 'USPS',
                    'services' => [
                        ['service' => 'Priority Mail', 'multiplier' => 0.9, 'days' => $distance < 300 ? 2 : ($distance < 800 ? 3 : 4), 'insurance' => false]
                    ]
                ]
            ];
            
            // Build flat options array with calculated costs and scores
            $options = [];
            foreach ($carriers as $carrier) {
                foreach ($carrier['services'] as $service) {
                    $cost = round(($base_cost + $distance_cost + $weight_cost) * $service['multiplier'] * $cost_multiplier, 2);
                    $delivery_date = date('Y-m-d', strtotime("+{$service['days']} days"));
                    
                    // Calculate value score based on priority setting
                    $cost_score = max(0, 100 - ($cost * 2)); // Penalize high cost
                    $speed_score = max(0, 100 - ($service['days'] * 20)); // Penalize slow delivery
                    
                    // Adjust weights based on shipping priority
                    if ($shipping_priority === 'cost') {
                        $value_score = ($cost_score * 0.8) + ($speed_score * 0.2); // 80% cost, 20% speed
                    } elseif ($shipping_priority === 'speed') {
                        $value_score = ($cost_score * 0.2) + ($speed_score * 0.8); // 20% cost, 80% speed
                    } else { // balanced
                        $value_score = ($cost_score * 0.6) + ($speed_score * 0.4); // 60% cost, 40% speed
                    }
                    
                    $options[] = [
                        'carrier' => $carrier['carrier'],
                        'service_level' => $service['service'],
                        'rate' => $cost,
                        'estimated_delivery_days' => $service['days'],
                        'delivery_date' => $delivery_date,
                        'reliability_score' => $base_reliability,
                        'insurance_included' => $service['insurance'],
                        'tracking' => true,
                        'value_score' => round($value_score, 1),
                        'recommended' => false // Will set after comparing all options
                    ];
                }
            }
            
            // Find the option with the best value score and mark it as recommended
            if (!empty($options)) {
                $best_score = max(array_column($options, 'value_score'));
                foreach ($options as &$option) {
                    if ($option['value_score'] === $best_score) {
                        $option['recommended'] = true;
                        break; // Only recommend one option
                    }
                }
                unset($option); // Break reference
            }
            
            echo json_encode([
                'order' => [
                    'id' => $order_id,
                    'shipping_address' => $order['shipping_address'] ?: 'Not specified',
                    'total_weight_lbs' => $weight,
                    'package_dimensions' => '10x8x6'
                ],
                'options' => $options
            ]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['error' => $e->getMessage()]);
        }
        exit;
    }
    
    // ========== FULFILLMENT ACTION ENDPOINTS ==========
    
    // Route: POST /api/orders/{orderId}/validate - Validate order (fraud check, address verification)
    if (preg_match('#^/api/orders/([^/]+)/validate$#', $request_uri, $matches) && $request_method === 'POST') {
        $order_id = $matches[1];
        $data = json_decode(file_get_contents('php://input'), true);
        
        try {
            $stmt = $db->prepare('SELECT * FROM orders WHERE id = ?');
            $stmt->execute([$order_id]);
            $order = $stmt->fetch(PDO::FETCH_ASSOC);
            
            if (!$order) {
                http_response_code(404);
                echo json_encode(['error' => 'Order not found']);
                exit;
            }
            
            // MANUAL PROCESS: Fraud detection and address verification
            // In reality, this would involve checking customer history, payment patterns, etc.
            $approved = $data['approved'] ?? true;
            $notes = $data['notes'] ?? 'Order validated - no fraud indicators detected';
            
            if ($approved) {
                update_order_status($db, $order_id, 'validated', $notes, $_SESSION['user']['username']);
                echo json_encode(['success' => true, 'message' => 'Order validated successfully']);
            } else {
                update_order_status($db, $order_id, 'validation_failed', $notes, $_SESSION['user']['username']);
                echo json_encode(['success' => false, 'message' => 'Order validation failed']);
            }
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['error' => $e->getMessage()]);
        }
        exit;
    }
    
    // Route: POST /api/orders/{orderId}/assign-warehouse - Assign order to warehouse
    if (preg_match('#^/api/orders/([^/]+)/assign-warehouse$#', $request_uri, $matches) && $request_method === 'POST') {
        $order_id = $matches[1];
        $data = json_decode(file_get_contents('php://input'), true);
        
        try {
            $warehouse_id = $data['warehouse_id'] ?? null;
            
            if (!$warehouse_id) {
                // Auto-select warehouse with lowest load
                $stmt = $db->query('SELECT id FROM warehouses ORDER BY current_load ASC LIMIT 1');
                $warehouse = $stmt->fetch(PDO::FETCH_ASSOC);
                $warehouse_id = $warehouse['id'];
            }
            
            $stmt = $db->prepare('UPDATE orders SET warehouse_id = ?, updated_at = ? WHERE id = ?');
            $stmt->execute([$warehouse_id, date('Y-m-d H:i:s'), $order_id]);
            
            $stmt = $db->prepare('UPDATE warehouses SET current_load = current_load + 1 WHERE id = ?');
            $stmt->execute([$warehouse_id]);
            
            update_order_status($db, $order_id, 'warehouse_assigned', "Assigned to warehouse $warehouse_id", $_SESSION['user']['username']);
            
            echo json_encode(['success' => true, 'warehouse_id' => $warehouse_id]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['error' => $e->getMessage()]);
        }
        exit;
    }
    
    // Route: POST /api/orders/{orderId}/pick - Mark order as picked
    if (preg_match('#^/api/orders/([^/]+)/pick$#', $request_uri, $matches) && $request_method === 'POST') {
        $order_id = $matches[1];
        $data = json_decode(file_get_contents('php://input'), true);
        
        try {
            $notes = $data['notes'] ?? 'Items picked from warehouse';
            update_order_status($db, $order_id, 'picking', $notes, $_SESSION['user']['username']);
            
            echo json_encode(['success' => true, 'message' => 'Order marked as picked']);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['error' => $e->getMessage()]);
        }
        exit;
    }
    
    // Route: POST /api/orders/{orderId}/pack - Mark order as packed
    if (preg_match('#^/api/orders/([^/]+)/pack$#', $request_uri, $matches) && $request_method === 'POST') {
        $order_id = $matches[1];
        $data = json_decode(file_get_contents('php://input'), true);
        
        try {
            $notes = $data['notes'] ?? 'Order packed and ready for quality check';
            update_order_status($db, $order_id, 'packed', $notes, $_SESSION['user']['username']);
            
            echo json_encode(['success' => true, 'message' => 'Order marked as packed']);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['error' => $e->getMessage()]);
        }
        exit;
    }
    
    // Route: POST /api/orders/{orderId}/quality-check - Perform quality check
    if (preg_match('#^/api/orders/([^/]+)/quality-check$#', $request_uri, $matches) && $request_method === 'POST') {
        $order_id = $matches[1];
        $data = json_decode(file_get_contents('php://input'), true);
        
        try {
            $passed = $data['passed'] ?? true;
            $notes = $data['notes'] ?? 'Quality check passed';
            
            if ($passed) {
                update_order_status($db, $order_id, 'quality_checked', $notes, $_SESSION['user']['username']);
                echo json_encode(['success' => true, 'message' => 'Quality check passed']);
            } else {
                update_order_status($db, $order_id, 'quality_failed', $notes, $_SESSION['user']['username']);
                echo json_encode(['success' => false, 'message' => 'Quality check failed']);
            }
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['error' => $e->getMessage()]);
        }
        exit;
    }
    
    // Route: POST /api/orders/{orderId}/ship - Generate shipping label and mark as shipped
    if (preg_match('#^/api/orders/([^/]+)/ship$#', $request_uri, $matches) && $request_method === 'POST') {
        $order_id = $matches[1];
        $data = json_decode(file_get_contents('php://input'), true);
        
        try {
            $carrier = $data['carrier'] ?? 'UPS';
            $tracking_number = $data['tracking_number'] ?? 'TRACK' . strtoupper(uniqid());
            
            $stmt = $db->prepare('UPDATE orders SET carrier = ?, tracking_number = ?, updated_at = ? WHERE id = ?');
            $stmt->execute([$carrier, $tracking_number, date('Y-m-d H:i:s'), $order_id]);
            
            update_order_status($db, $order_id, 'shipped', "Shipped via $carrier - Tracking: $tracking_number", $_SESSION['user']['username']);
            
            echo json_encode(['success' => true, 'tracking_number' => $tracking_number, 'carrier' => $carrier]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['error' => $e->getMessage()]);
        }
        exit;
    }
    
    // Route: POST /api/orders/{orderId}/deliver - Mark order as delivered
    if (preg_match('#^/api/orders/([^/]+)/deliver$#', $request_uri, $matches) && $request_method === 'POST') {
        $order_id = $matches[1];
        $data = json_decode(file_get_contents('php://input'), true);
        
        try {
            $notes = $data['notes'] ?? 'Package delivered successfully';
            update_order_status($db, $order_id, 'delivered', $notes, 'carrier');
            
            echo json_encode(['success' => true, 'message' => 'Order marked as delivered']);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['error' => $e->getMessage()]);
        }
        exit;
    }
    
    // Route: POST /api/orders/{orderId}/confirm-delivery - Customer confirms delivery receipt
    if (preg_match('#^/api/orders/([^/]+)/confirm-delivery$#', $request_uri, $matches) && $request_method === 'POST') {
        $order_id = $matches[1];
        
        try {
            // Verify order exists and is in shipped status
            $stmt = $db->prepare('SELECT * FROM orders WHERE id = ?');
            $stmt->execute([$order_id]);
            $order = $stmt->fetch(PDO::FETCH_ASSOC);
            
            if (!$order) {
                http_response_code(404);
                echo json_encode(['error' => 'Order not found']);
                exit;
            }
            
            if ($order['status'] !== 'shipped') {
                http_response_code(400);
                echo json_encode(['error' => 'Order must be in shipped status to confirm delivery']);
                exit;
            }
            
            // Update order status to delivered
            update_order_status($db, $order_id, 'delivered', 'Customer confirmed delivery', $_SESSION['user']['username']);
            
            echo json_encode(['success' => true, 'message' => 'Delivery confirmed successfully']);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['error' => $e->getMessage()]);
        }
        exit;
    }
    
    // Route: GET /api/orders/{orderId}/history - Get order status history
    if (preg_match('#^/api/orders/([^/]+)/history$#', $request_uri, $matches) && $request_method === 'GET') {
        $order_id = $matches[1];
        
        try {
            $stmt = $db->prepare('SELECT * FROM order_status_history WHERE order_id = ? ORDER BY created_at ASC');
            $stmt->execute([$order_id]);
            $history = $stmt->fetchAll(PDO::FETCH_ASSOC);
            
            echo json_encode(['history' => $history]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['error' => $e->getMessage()]);
        }
        exit;
    }
    
    // Route: GET /api/admin/orders/pending-fulfillment - Get orders needing fulfillment actions
    if ($request_uri === '/api/admin/orders/pending-fulfillment' && $request_method === 'GET') {
        if ($_SESSION['user']['role'] !== 'admin') {
            http_response_code(403);
            echo json_encode(['error' => 'Forbidden - Admin access required']);
            exit;
        }
        
        try {
            $stmt = $db->query('SELECT * FROM orders WHERE status IN ("confirmed", "validated", "warehouse_assigned", "picking", "packed", "quality_checked") ORDER BY created_at ASC');
            $orders = $stmt->fetchAll(PDO::FETCH_ASSOC);
            
            echo json_encode(['orders' => $orders]);
        } catch (Exception $e) {
            http_response_code(500);
            echo json_encode(['error' => $e->getMessage()]);
        }
        exit;
    }

    // Route: GET /api/orders/me - Get current user's orders
    if ($request_uri === '/api/orders/me' && $request_method === 'GET') {
        $customer_id = $_SESSION['user']['id'];
        $stmt = $db->prepare('SELECT * FROM orders WHERE customer_id = ? ORDER BY created_at DESC');
        $stmt->execute([$customer_id]);
        $orders = $stmt->fetchAll(PDO::FETCH_ASSOC);
        echo json_encode(['orders' => $orders]);
        exit;
    }

    // Route: GET /api/orders/customer/{customerId} - Get customer orders (catch-all moved here)
    if (preg_match('#^/api/orders/customer/(.+)$#', $request_uri, $matches) && $request_method === 'GET') {
        $customer_id = $_SESSION['user']['id'];
        $stmt = $db->prepare('SELECT * FROM orders WHERE customer_id = ? ORDER BY created_at DESC');
        $stmt->execute([$customer_id]);
        $orders = $stmt->fetchAll(PDO::FETCH_ASSOC);
        echo json_encode(['orders' => $orders]);
        exit;
    }

    
    if ($request_uri === '/api/returns' && $request_method === 'POST') {
        $data = json_decode(file_get_contents('php://input'), true);
        $db->beginTransaction();
        try {
            $stmt = $db->prepare('SELECT * FROM orders WHERE id = ?');
            $stmt->execute([$data['order_id']]);
            $order = $stmt->fetch(PDO::FETCH_ASSOC);
            if (!$order) throw new Exception('Order not found');
            
            // MANUAL PROCESS: Return requests require manual review and approval
            // In the monolith, there's no way to safely automate this without risking:
            // - Inventory corruption across all domains
            // - Payment processing errors affecting other transactions
            // - Order status inconsistencies
            
            $return_id = uniqid('return-');
            $stmt = $db->prepare('INSERT INTO returns VALUES (?, ?, ?, ?, ?, ?, ?)');
            $stmt->execute([$return_id, $data['order_id'], $data['reason'], 'pending_review', 
                null, date('Y-m-d H:i:s'), null]);
            
            $stmt = $db->prepare('INSERT INTO interactions VALUES (?, ?, ?, ?, ?, ?, ?)');
            $stmt->execute([uniqid('int-'), $order['customer_id'], $data['order_id'], 
                'return_request', 'Customer requested return: ' . $data['reason'], 
                'neutral', date('Y-m-d H:i:s')]);
            
            $db->commit();
            echo json_encode([
                'success' => true, 
                'return_id' => $return_id,
                'status' => 'pending_review',
                'message' => 'Return request submitted. A customer service representative will review your request within 24-48 hours and contact you via email.'
            ]);
        } catch (Exception $e) {
            $db->rollBack();
            http_response_code(400);
            echo json_encode(['error' => $e->getMessage()]);
        }
        exit;
    }
    
    // Get pending returns for admin review
    if ($request_uri === '/api/admin/pending-returns' && $request_method === 'GET') {
        if ($_SESSION['user']['role'] !== 'admin') {
            http_response_code(403);
            echo json_encode(['error' => 'Forbidden - Admin access required']);
            exit;
        }
        $stmt = $db->query('SELECT r.*, o.customer_name, o.customer_email, o.total_amount 
            FROM returns r 
            JOIN orders o ON r.order_id = o.id 
            WHERE r.status = "pending_review" 
            ORDER BY r.created_at DESC');
        $returns = $stmt->fetchAll(PDO::FETCH_ASSOC);
        echo json_encode(['returns' => $returns]);
        exit;
    }
    
    // MANUAL ADMIN ENDPOINT: Approve returns (simulates manual CS rep work)
    if ($request_uri === '/api/admin/approve-return' && $request_method === 'POST') {
        if ($_SESSION['user']['role'] !== 'admin') {
            http_response_code(403);
            echo json_encode(['error' => 'Forbidden - Admin access required']);
            exit;
        }
        $data = json_decode(file_get_contents('php://input'), true);
        $db->beginTransaction();
        try {
            $stmt = $db->prepare('SELECT * FROM returns WHERE id = ?');
            $stmt->execute([$data['return_id']]);
            $return = $stmt->fetch(PDO::FETCH_ASSOC);
            if (!$return) throw new Exception('Return not found');
            
            $stmt = $db->prepare('SELECT * FROM orders WHERE id = ?');
            $stmt->execute([$return['order_id']]);
            $order = $stmt->fetch(PDO::FETCH_ASSOC);
            
            $stmt = $db->prepare('SELECT * FROM order_items WHERE order_id = ?');
            $stmt->execute([$return['order_id']]);
            $items = $stmt->fetchAll(PDO::FETCH_ASSOC);
            
            // Process refund
            $stmt = $db->prepare('UPDATE returns SET status = ?, refund_amount = ?, processed_at = ? WHERE id = ?');
            $stmt->execute(['approved', $order['total_amount'], date('Y-m-d H:i:s'), $data['return_id']]);
            
            // Restore inventory
            foreach ($items as $item) {
                $stmt = $db->prepare('UPDATE inventory SET stock_quantity = stock_quantity + ? WHERE product_id = ?');
                $stmt->execute([$item['quantity'], $item['product_id']]);
            }
            
            // Issue refund
            $stmt = $db->prepare('INSERT INTO payments VALUES (?, ?, ?, ?, ?, ?)');
            $stmt->execute([uniqid('refund-'), $return['order_id'], -$order['total_amount'], 
                'refund', 'completed', date('Y-m-d H:i:s')]);
            
            // Update order status
            $stmt = $db->prepare('UPDATE orders SET status = ?, updated_at = ? WHERE id = ?');
            $stmt->execute(['returned', date('Y-m-d H:i:s'), $return['order_id']]);
            
            $db->commit();
            echo json_encode(['success' => true, 'message' => 'Return approved and refund processed']);
        } catch (Exception $e) {
            $db->rollBack();
            http_response_code(400);
            echo json_encode(['error' => $e->getMessage()]);
        }
        exit;
    }
    
    // ========== USER MANAGEMENT ENDPOINTS ==========
    
    // Route: GET /api/admin/users - Get all users
    if ($request_uri === '/api/admin/users' && $request_method === 'GET') {
        if ($current_user['role'] !== 'admin') {
            http_response_code(403);
            echo json_encode(['error' => 'Admin access required']);
            exit;
        }
        
        $stmt = $db->query('SELECT id, username, name, email, role, created_at FROM users ORDER BY created_at DESC');
        $users = $stmt->fetchAll(PDO::FETCH_ASSOC);
        echo json_encode(['users' => $users]);
        exit;
    }
    
    // Route: POST /api/admin/users - Create new user
    if ($request_uri === '/api/admin/users' && $request_method === 'POST') {
        if ($current_user['role'] !== 'admin') {
            http_response_code(403);
            echo json_encode(['error' => 'Admin access required']);
            exit;
        }
        
        $data = json_decode(file_get_contents('php://input'), true);
        
        // Validate required fields
        if (empty($data['username']) || empty($data['password']) || empty($data['name']) || empty($data['email']) || empty($data['role'])) {
            http_response_code(400);
            echo json_encode(['error' => 'All fields are required']);
            exit;
        }
        
        // Check if username already exists
        $stmt = $db->prepare('SELECT id FROM users WHERE username = ?');
        $stmt->execute([$data['username']]);
        if ($stmt->fetch()) {
            http_response_code(400);
            echo json_encode(['error' => 'Username already exists']);
            exit;
        }
        
        // Check if email already exists
        $stmt = $db->prepare('SELECT id FROM users WHERE email = ?');
        $stmt->execute([$data['email']]);
        if ($stmt->fetch()) {
            http_response_code(400);
            echo json_encode(['error' => 'Email already exists']);
            exit;
        }
        
        try {
            $user_id = uniqid('user-');
            $password_hash = password_hash($data['password'], PASSWORD_DEFAULT);
            
            $stmt = $db->prepare('INSERT INTO users (id, username, password, name, email, role, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)');
            $stmt->execute([
                $user_id,
                $data['username'],
                $password_hash,
                $data['name'],
                $data['email'],
                $data['role'],
                date('Y-m-d H:i:s')
            ]);
            
            echo json_encode(['success' => true, 'user_id' => $user_id, 'message' => 'User created successfully']);
        } catch (Exception $e) {
            http_response_code(400);
            echo json_encode(['error' => $e->getMessage()]);
        }
        exit;
    }
    
    // Route: PUT /api/admin/users/{id} - Update user
    if (preg_match('#^/api/admin/users/([^/]+)$#', $request_uri, $matches) && $request_method === 'PUT') {
        if ($current_user['role'] !== 'admin') {
            http_response_code(403);
            echo json_encode(['error' => 'Admin access required']);
            exit;
        }
        
        $user_id = $matches[1];
        $data = json_decode(file_get_contents('php://input'), true);
        
        // Check if user exists
        $stmt = $db->prepare('SELECT * FROM users WHERE id = ?');
        $stmt->execute([$user_id]);
        $user = $stmt->fetch(PDO::FETCH_ASSOC);
        
        if (!$user) {
            http_response_code(404);
            echo json_encode(['error' => 'User not found']);
            exit;
        }
        
        try {
            $updates = [];
            $params = [];
            
            if (isset($data['name'])) {
                $updates[] = 'name = ?';
                $params[] = $data['name'];
            }
            if (isset($data['email'])) {
                // Check if email is taken by another user
                $stmt = $db->prepare('SELECT id FROM users WHERE email = ? AND id != ?');
                $stmt->execute([$data['email'], $user_id]);
                if ($stmt->fetch()) {
                    http_response_code(400);
                    echo json_encode(['error' => 'Email already exists']);
                    exit;
                }
                $updates[] = 'email = ?';
                $params[] = $data['email'];
            }
            if (isset($data['role'])) {
                $updates[] = 'role = ?';
                $params[] = $data['role'];
            }
            if (isset($data['password']) && !empty($data['password'])) {
                $updates[] = 'password = ?';
                $params[] = password_hash($data['password'], PASSWORD_DEFAULT);
            }
            
            if (empty($updates)) {
                http_response_code(400);
                echo json_encode(['error' => 'No fields to update']);
                exit;
            }
            
            $params[] = $user_id;
            $sql = 'UPDATE users SET ' . implode(', ', $updates) . ' WHERE id = ?';
            $stmt = $db->prepare($sql);
            $stmt->execute($params);
            
            echo json_encode(['success' => true, 'message' => 'User updated successfully']);
        } catch (Exception $e) {
            http_response_code(400);
            echo json_encode(['error' => $e->getMessage()]);
        }
        exit;
    }
    
    // Route: DELETE /api/admin/users/{id} - Delete user
    if (preg_match('#^/api/admin/users/([^/]+)$#', $request_uri, $matches) && $request_method === 'DELETE') {
        if ($current_user['role'] !== 'admin') {
            http_response_code(403);
            echo json_encode(['error' => 'Admin access required']);
            exit;
        }
        
        $user_id = $matches[1];
        
        // Prevent deleting yourself
        if ($user_id === $current_user['id']) {
            http_response_code(400);
            echo json_encode(['error' => 'Cannot delete your own account']);
            exit;
        }
        
        // Check if user exists
        $stmt = $db->prepare('SELECT * FROM users WHERE id = ?');
        $stmt->execute([$user_id]);
        $user = $stmt->fetch(PDO::FETCH_ASSOC);
        
        if (!$user) {
            http_response_code(404);
            echo json_encode(['error' => 'User not found']);
            exit;
        }
        
        try {
            $stmt = $db->prepare('DELETE FROM users WHERE id = ?');
            $stmt->execute([$user_id]);
            
            echo json_encode(['success' => true, 'message' => 'User deleted successfully']);
        } catch (Exception $e) {
            http_response_code(400);
            echo json_encode(['error' => $e->getMessage()]);
        }
        exit;
    }
    
    http_response_code(404);
    echo json_encode(['error' => 'Not found']);
    exit;
}

// Show login page if not authenticated
if (!isset($_SESSION['user'])) {
    $login_error = $_SESSION['login_error'] ?? '';
    unset($_SESSION['login_error']);
    ?>
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login - E-Commerce Monolith</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
            .login-container { background: white; border-radius: 8px; padding: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }
            .login-header { text-align: center; margin-bottom: 2rem; }
            .login-header h1 { font-size: 1.5rem; color: #232f3e; margin-bottom: 0.5rem; }
            .login-header .subtitle { font-size: 0.875rem; color: #666; }
            .form-group { margin-bottom: 1.5rem; }
            .form-group label { display: block; margin-bottom: 0.5rem; font-weight: 500; color: #232f3e; }
            .form-group input { width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 4px; font-size: 1rem; }
            .form-group input:focus { outline: none; border-color: #ff9900; }
            .btn { width: 100%; background: #ff9900; color: white; border: none; padding: 0.75rem; border-radius: 4px; cursor: pointer; font-size: 1rem; font-weight: 500; }
            .btn:hover { background: #ec7211; }
            .alert { padding: 1rem; border-radius: 4px; margin-bottom: 1rem; background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .demo-credentials { background: #e7f3ff; border: 2px solid #2196F3; border-radius: 8px; padding: 1rem; margin-top: 1.5rem; font-size: 0.875rem; }
            .demo-credentials h3 { color: #1976D2; margin-bottom: 0.5rem; font-size: 0.875rem; }
            .demo-credentials .cred { margin: 0.5rem 0; padding: 0.5rem; background: white; border-radius: 4px; font-family: monospace; }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="login-header">
                <h1>🏪 E-Commerce Monolith</h1>
                <div class="subtitle">Login to Continue</div>
            </div>
            
            <?php if ($login_error): ?>
                <div class="alert"><?php echo htmlspecialchars($login_error); ?></div>
            <?php endif; ?>
            
            <form method="POST" action="/login">
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" name="username" required autofocus>
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" name="password" required>
                </div>
                <button type="submit" class="btn">Login</button>
            </form>
            
            <div class="demo-credentials">
                <h3>📋 Demo Credentials</h3>
                <div class="cred"><strong>Customer:</strong> customer / customer123</div>
                <div class="cred"><strong>Admin:</strong> admin / admin123</div>
            </div>
        </div>
    </body>
    </html>
    <?php
    exit;
}

// $current_user is already set at the top of the file after session_start()
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E-Commerce Monolith</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; }
        .header { background: #232f3e; color: white; padding: 1rem 2rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header h1 { font-size: 1.5rem; font-weight: 600; }
        .header .subtitle { font-size: 0.875rem; color: #ff9900; margin-top: 0.25rem; }
        .container { max-width: 1200px; margin: 2rem auto; padding: 0 1rem; }
        .tabs { display: flex; gap: 1rem; margin-bottom: 2rem; border-bottom: 2px solid #ddd; }
        .tab { padding: 0.75rem 1.5rem; background: none; border: none; cursor: pointer; font-size: 1rem; color: #666; border-bottom: 3px solid transparent; }
        .tab:hover { color: #232f3e; }
        .tab.active { color: #232f3e; border-bottom-color: #ff9900; }
        .admin-subtab { padding: 0.5rem 1rem; background: none; border: none; cursor: pointer; font-size: 0.875rem; color: #666; border-bottom: 3px solid transparent; }
        .admin-subtab:hover { color: #232f3e; }
        .admin-subtab.active { color: #232f3e; border-bottom-color: #ff9900; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .products-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1.5rem; }
        .product-card { background: white; border-radius: 8px; padding: 1.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .product-card h3 { font-size: 1.125rem; margin-bottom: 0.5rem; }
        .product-card .price { font-size: 1.5rem; color: #ff9900; font-weight: 600; margin: 0.5rem 0; }
        .product-card .stock { font-size: 0.875rem; color: #666; margin-bottom: 1rem; }
        .btn { background: #ff9900; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 4px; cursor: pointer; font-size: 1rem; }
        .btn:hover { background: #ec7211; }
        .btn:disabled { background: #ccc; cursor: not-allowed; }
        .form-group { margin-bottom: 1.5rem; }
        .form-group label { display: block; margin-bottom: 0.5rem; font-weight: 500; }
        .form-group input, .form-group textarea { width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 4px; font-size: 1rem; }
        .order-card { background: white; border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .order-header { display: flex; justify-content: space-between; margin-bottom: 1rem; padding-bottom: 1rem; border-bottom: 1px solid #eee; }
        .status-badge { padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.875rem; font-weight: 500; }
        .status-delivered { background: #d4edda; color: #155724; }
        .status-confirmed { background: #d1ecf1; color: #0c5460; }
        .status-returned { background: #f8d7da; color: #721c24; }
        .alert { padding: 1rem; border-radius: 4px; margin-bottom: 1rem; }
        .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .warning-box { background: #fff3cd; border: 2px solid #ffc107; border-radius: 8px; padding: 1.5rem; margin-bottom: 2rem; }
        .warning-box h3 { color: #856404; margin-bottom: 0.5rem; }
        .warning-box ul { margin-left: 1.5rem; color: #856404; }
        .db-info { background: #e7f3ff; border: 2px solid #2196F3; border-radius: 8px; padding: 1rem; margin-bottom: 2rem; font-size: 0.875rem; }
        .db-info strong { color: #1976D2; }
    </style>
</head>
<body>
    <div class="header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1>🏪 E-Commerce Monolith</h1>
                <div class="subtitle">Tightly Coupled Architecture - All Domains in One Application</div>
            </div>
            <div style="display: flex; align-items: center; gap: 1rem;">
                <div style="color: white; font-size: 0.875rem;">
                    👤 <?php echo htmlspecialchars($current_user['name']); ?> 
                    <span style="color: #ff9900;">(<?php echo htmlspecialchars($current_user['role']); ?>)</span>
                </div>
                <a href="/logout" style="color: white; text-decoration: none; padding: 0.5rem 1rem; background: rgba(255,255,255,0.1); border-radius: 4px; font-size: 0.875rem;">Logout</a>
            </div>
        </div>
    </div>
    
    <div class="container">
        <div class="db-info">
            <strong>🗄️ Database:</strong> MySQL (Shared database for all domains - Orders, Inventory, Payments, Returns)
        </div>
        
        <div class="warning-box">
            <h3>⚠️ Monolithic Architecture Constraints</h3>
            <ul>
                <li>All business logic tightly coupled in single codebase</li>
                <li>Shared MySQL database creates risk for AI operations</li>
                <li>No clear API boundaries for agent interaction</li>
                <li>Cannot scale domains independently</li>
                <li><strong>Returns require manual CS review (24-48 hours) - perfect AI automation candidate!</strong></li>
            </ul>
        </div>
        
        <div class="tabs">
            <?php if ($current_user['role'] === 'customer'): ?>
            <button class="tab active" onclick="showTab('products')">Products</button>
            <button class="tab" onclick="showTab('orders')">My Orders</button>
            <button class="tab" onclick="showTab('returns')">Returns</button>
            <?php endif; ?>
            <?php if ($current_user['role'] === 'admin'): ?>
            <button class="tab active" onclick="showTab('admin')" style="background: #ff9900; color: white;">🔧 Admin Panel</button>
            <?php endif; ?>
        </div>
        
        <?php if ($current_user['role'] === 'customer'): ?>
        <div id="products-tab" class="tab-content active">
            <h2 style="margin-bottom: 1.5rem;">Available Products</h2>
            <div id="products-grid" class="products-grid"></div>
        </div>
        
        <div id="orders-tab" class="tab-content">
            <h2 style="margin-bottom: 1.5rem;">My Orders</h2>
            <div id="orders-list"></div>
        </div>
        
        <div id="returns-tab" class="tab-content">
            <h2 style="margin-bottom: 1.5rem;">Process Return</h2>
            <div id="return-message"></div>
            <div class="order-card">
                <div class="form-group">
                    <label>Order ID</label>
                    <input type="text" id="return-order-id" placeholder="Enter order ID">
                </div>
                <div class="form-group">
                    <label>Reason for Return</label>
                    <textarea id="return-reason" rows="4" placeholder="Describe why you're returning this order"></textarea>
                </div>
                <button class="btn" onclick="processReturn()">Process Return</button>
            </div>
        </div>
        <?php endif; ?>
        
        <?php if ($current_user['role'] === 'admin'): ?>

        <div id="admin-tab" class="tab-content">
            <h2 style="margin-bottom: 1.5rem;">🔧 Admin Panel</h2>
            
            <!-- Admin Sub-tabs -->
            <div style="display: flex; gap: 0.5rem; margin-bottom: 2rem; border-bottom: 2px solid #ddd; padding-bottom: 0.5rem;">
                <button class="admin-subtab active" onclick="showAdminSubTab('fulfillment')" style="padding: 0.5rem 1rem; background: none; border: none; cursor: pointer; font-size: 0.875rem; color: #666; border-bottom: 3px solid transparent;">📦 Fulfillment</button>
                <button class="admin-subtab" onclick="showAdminSubTab('controls')" style="padding: 0.5rem 1rem; background: none; border: none; cursor: pointer; font-size: 0.875rem; color: #666; border-bottom: 3px solid transparent;">🎛️ AI Controls</button>
                <button class="admin-subtab" onclick="showAdminSubTab('users')" style="padding: 0.5rem 1rem; background: none; border: none; cursor: pointer; font-size: 0.875rem; color: #666; border-bottom: 3px solid transparent;">👥 Users</button>
                <button class="admin-subtab" onclick="showAdminSubTab('returns')" style="padding: 0.5rem 1rem; background: none; border: none; cursor: pointer; font-size: 0.875rem; color: #666; border-bottom: 3px solid transparent;">↩️ Returns</button>
            </div>
            
            <!-- Fulfillment Sub-tab -->
            <div id="admin-fulfillment-subtab" class="admin-subtab-content" style="display: block;">
                <h3 style="margin-bottom: 1.5rem;">📦 Order Fulfillment Workflow</h3>
                <div class="warning-box" style="background: #fff3cd; border-color: #ffc107;">
                    <h3 style="color: #856404;">⚠️ Manual Fulfillment Process</h3>
                    <p style="color: #856404; margin-top: 0.5rem;">Each step requires manual intervention by warehouse staff, operations managers, or CS reps. This is the pain point that AI agents will automate in the microservices architecture.</p>
                </div>
                <div id="fulfillment-message"></div>
                <div id="fulfillment-orders-list"></div>
            </div>
            
            <!-- AI Controls Sub-tab -->
            <div id="admin-controls-subtab" class="admin-subtab-content" style="display: none;">
                <h3 style="margin-bottom: 1.5rem;">🎛️ AI Decision Control Panel</h3>
                <div class="warning-box" style="background: #e7f3ff; border-color: #2196F3;">
                    <h3 style="color: #1976D2;">💡 Simulate Different Scenarios</h3>
                    <p style="color: #1976D2; margin-top: 0.5rem;">Adjust these parameters to see how an AI agent would make different decisions in the fulfillment workflow. This helps demonstrate the agent's decision-making capabilities under various conditions.</p>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 1.5rem;">
                    <!-- Warehouse Controls -->
                    <div class="order-card">
                        <h3 style="margin-bottom: 1rem; color: #ff9900;">🏭 Warehouse Conditions</h3>
                        <div class="form-group">
                            <label>Seattle Warehouse Load (%)</label>
                            <input type="range" id="wh-seattle-load" min="0" max="100" value="0" oninput="document.getElementById('wh-seattle-val').textContent = this.value + '%'">
                            <span id="wh-seattle-val" style="font-weight: bold;">0%</span>
                        </div>
                        <div class="form-group">
                            <label>Portland Warehouse Load (%)</label>
                            <input type="range" id="wh-portland-load" min="0" max="100" value="0" oninput="document.getElementById('wh-portland-val').textContent = this.value + '%'">
                            <span id="wh-portland-val" style="font-weight: bold;">0%</span>
                        </div>
                        <div class="form-group">
                            <label>San Francisco Warehouse Load (%)</label>
                            <input type="range" id="wh-sf-load" min="0" max="100" value="0" oninput="document.getElementById('wh-sf-val').textContent = this.value + '%'">
                            <span id="wh-sf-val" style="font-weight: bold;">0%</span>
                        </div>
                        <button class="btn" onclick="updateWarehouseLoads()">Apply Warehouse Changes</button>
                    </div>
                    
                    <!-- Picker Controls -->
                    <div class="order-card">
                        <h3 style="margin-bottom: 1rem; color: #ff9900;">👷 Picker Availability</h3>
                        <div class="form-group">
                            <label>Mike Johnson Status</label>
                            <select id="picker-mike" onchange="updatePickerStatuses()" style="width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px;">
                                <option value="Available">Available</option>
                                <option value="On Break">On Break</option>
                                <option value="Busy">Busy</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Sarah Chen Status</label>
                            <select id="picker-sarah" onchange="updatePickerStatuses()" style="width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px;">
                                <option value="Available">Available</option>
                                <option value="On Break">On Break</option>
                                <option value="Busy">Busy</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>David Martinez Status</label>
                            <select id="picker-david" onchange="updatePickerStatuses()" style="width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px;">
                                <option value="Available">Available</option>
                                <option value="On Break" selected>On Break</option>
                                <option value="Busy">Busy</option>
                            </select>
                        </div>
                        <p style="font-size: 0.875rem; color: #666; margin-top: 0.5rem;">Note: Picker status changes will be reflected in the next order picking workflow.</p>
                    </div>
                    
                    <!-- Shipping Controls -->
                    <div class="order-card">
                        <h3 style="margin-bottom: 1rem; color: #ff9900;">📦 Shipping Modifiers</h3>
                        <div class="form-group">
                            <label>Base Shipping Cost Multiplier</label>
                            <input type="range" id="shipping-multiplier" min="0.5" max="2.0" step="0.1" value="1.0" oninput="document.getElementById('shipping-mult-val').textContent = this.value + 'x'" onchange="updateShippingSettings()">
                            <span id="shipping-mult-val" style="font-weight: bold;">1.0x</span>
                        </div>
                        <div class="form-group">
                            <label>Carrier Reliability Override</label>
                            <select id="carrier-reliability" style="width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px;" onchange="updateShippingSettings()">
                                <option value="normal">Normal (98%)</option>
                                <option value="high">High Season (95%)</option>
                                <option value="weather">Weather Issues (90%)</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Priority Shipping Preference</label>
                            <select id="shipping-priority" style="width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px;" onchange="updateShippingSettings()">
                                <option value="balanced">Balanced (Cost + Speed)</option>
                                <option value="cost">Cost Optimized</option>
                                <option value="speed">Speed Optimized</option>
                            </select>
                        </div>
                        <p style="font-size: 0.875rem; color: #666; margin-top: 0.5rem;">These settings affect which shipping option the AI agent recommends.</p>
                    </div>
                    
                    <!-- Quality Check Controls -->
                    <div class="order-card">
                        <h3 style="margin-bottom: 1rem; color: #ff9900;">✅ Quality Standards</h3>
                        <div class="form-group">
                            <label>Inspection Strictness</label>
                            <select id="qc-strictness" style="width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px;" onchange="updateQCSettings()">
                                <option value="standard">Standard</option>
                                <option value="high">High (Premium Orders)</option>
                                <option value="expedited">Expedited (Fast Track)</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Auto-Pass Threshold</label>
                            <input type="range" id="qc-threshold" min="0" max="100" value="100" oninput="document.getElementById('qc-threshold-val').textContent = this.value + '%'" onchange="updateQCSettings()">
                            <span id="qc-threshold-val" style="font-weight: bold;">100%</span>
                            <p style="font-size: 0.75rem; color: #666; margin-top: 0.25rem;">Percentage of checks that must pass for auto-approval</p>
                        </div>
                        <p style="font-size: 0.875rem; color: #666; margin-top: 0.5rem;">Lower thresholds allow AI to auto-approve with fewer checks passed.</p>
                    </div>
                </div>
                
                <div class="order-card" style="margin-top: 1.5rem; background: #f8f9fa;">
                    <h3 style="margin-bottom: 1rem;">📊 Current Configuration Summary</h3>
                    <div id="config-summary" style="font-family: monospace; font-size: 0.875rem; background: white; padding: 1rem; border-radius: 4px; white-space: pre-wrap;">
Loading configuration...
                    </div>
                    <button class="btn" onclick="loadConfigSummary()" style="margin-top: 1rem; background: #6c757d;">🔄 Refresh Summary</button>
                </div>
            </div>
            
            <!-- Users Sub-tab -->
            <div id="admin-users-subtab" class="admin-subtab-content" style="display: none;">
                <h3 style="margin-bottom: 1.5rem;">👥 User Management</h3>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                    <p style="color: #666;">Manage user accounts and assign roles</p>
                    <button class="btn" onclick="showCreateUserForm()" style="background: #28a745;">➕ Create New User</button>
                </div>
                
                <div id="user-form" style="display: none; background: white; border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h3 id="user-form-title" style="margin-bottom: 1rem;">Create New User</h3>
                    <div id="user-message"></div>
                    <input type="hidden" id="edit-user-id">
                    <div class="form-group">
                        <label>Username</label>
                        <input type="text" id="user-username" placeholder="username" required>
                    </div>
                    <div class="form-group">
                        <label>Full Name</label>
                        <input type="text" id="user-name" placeholder="John Doe" required>
                    </div>
                    <div class="form-group">
                        <label>Email</label>
                        <input type="email" id="user-email" placeholder="john@example.com" required>
                    </div>
                    <div class="form-group">
                        <label>Password <span id="password-optional" style="color: #666; font-size: 0.875rem;"></span></label>
                        <input type="password" id="user-password" placeholder="Enter password">
                    </div>
                    <div class="form-group">
                        <label>Role</label>
                        <select id="user-role" style="width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 4px; font-size: 1rem;">
                            <option value="customer">Customer</option>
                            <option value="admin">Admin</option>
                        </select>
                    </div>
                    <div style="display: flex; gap: 1rem;">
                        <button class="btn" onclick="saveUser()" style="flex: 1; background: #28a745;">💾 Save User</button>
                        <button class="btn" onclick="cancelUserForm()" style="flex: 1; background: #6c757d;">Cancel</button>
                    </div>
                </div>
                
                <div id="users-list"></div>
            </div>
            
            <!-- Returns Sub-tab -->
            <div id="admin-returns-subtab" class="admin-subtab-content" style="display: none;">
                <h3 style="margin-bottom: 1.5rem;">↩️ Manual Return Reviews</h3>
                <div class="warning-box" style="background: #fff3cd; border-color: #ffc107;">
                    <h3 style="color: #856404;">⚠️ Manual Process Simulation</h3>
                    <p style="color: #856404; margin-top: 0.5rem;">This simulates the manual work a CS representative must do in the monolith. In the microservices architecture, an AI agent will handle this autonomously in seconds.</p>
                </div>
                <div id="admin-message"></div>
                <div id="pending-returns-list"></div>
            </div>
        </div>
        <?php endif; ?>
    </div>

    
    <script>
        function showTab(tabName) {
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById(tabName + '-tab').classList.add('active');
            if (tabName === 'products') loadProducts();
            else if (tabName === 'orders') loadOrders();
            else if (tabName === 'admin') {
                // Initialize admin panel with first sub-tab
                showAdminSubTab('fulfillment');
            }
        }
        
        function showAdminSubTab(subtabName) {
            // Update sub-tab buttons
            document.querySelectorAll('.admin-subtab').forEach(btn => {
                btn.classList.remove('active');
                btn.style.borderBottom = '3px solid transparent';
                btn.style.color = '#666';
            });
            
            // Find and activate the clicked button
            const clickedBtn = document.querySelector(`.admin-subtab[onclick*="${subtabName}"]`);
            if (clickedBtn) {
                clickedBtn.classList.add('active');
                clickedBtn.style.borderBottom = '3px solid #ff9900';
                clickedBtn.style.color = '#232f3e';
            }
            
            // Update sub-tab content
            document.querySelectorAll('.admin-subtab-content').forEach(content => {
                content.style.display = 'none';
            });
            const subtabContent = document.getElementById('admin-' + subtabName + '-subtab');
            if (subtabContent) {
                subtabContent.style.display = 'block';
            }
            
            // Load data for the selected sub-tab
            if (subtabName === 'fulfillment') loadFulfillmentOrders();
            else if (subtabName === 'controls') loadConfigSummary();
            else if (subtabName === 'users') loadUsers();
            else if (subtabName === 'returns') loadPendingReturns();
        }
        
        // Auto-load initial content based on user role
        window.addEventListener('DOMContentLoaded', function() {
            const isAdmin = <?php echo json_encode($current_user['role'] === 'admin'); ?>;
            if (isAdmin) {
                showAdminSubTab('fulfillment');
            } else {
                loadProducts();
            }
        });
        
        async function loadFulfillmentOrders() {
            const response = await fetch('/api/admin/orders/pending-fulfillment');
            const data = await response.json();
            const list = document.getElementById('fulfillment-orders-list');
            if (data.orders.length === 0) {
                list.innerHTML = '<div class="order-card"><p>No orders pending fulfillment.</p></div>';
                return;
            }
            list.innerHTML = data.orders.map(order => {
                const statusActions = getStatusActions(order.status, order.id);
                return `
                    <div class="order-card">
                        <div class="order-header">
                            <div>
                                <strong>Order ID:</strong> ${order.id}<br>
                                <strong>Customer:</strong> ${order.customer_name}<br>
                                <strong>Total:</strong> $${parseFloat(order.total_amount).toFixed(2)}<br>
                                <strong>Created:</strong> ${new Date(order.created_at).toLocaleString()}
                            </div>
                            <div><span class="status-badge" style="background: #fff3cd; color: #856404;">${order.status}</span></div>
                        </div>
                        ${order.warehouse_id ? `<div style="margin: 0.5rem 0;"><strong>Warehouse:</strong> ${order.warehouse_id}</div>` : ''}
                        ${order.tracking_number ? `<div style="margin: 0.5rem 0;"><strong>Tracking:</strong> ${order.tracking_number} (${order.carrier})</div>` : ''}
                        <div style="margin-top: 1rem; display: flex; gap: 0.5rem; flex-wrap: wrap;">
                            ${statusActions}
                        </div>
                        <button class="btn" style="margin-top: 0.5rem; background: #6c757d;" onclick="viewOrderHistory('${order.id}')">📋 View History</button>
                    </div>
                `;
            }).join('');
        }
        
        function getStatusActions(status, orderId) {
            const actions = {
                'confirmed': `<button class="btn" onclick="validateOrder('${orderId}')">✅ Validate Order</button>`,
                'validated': `<button class="btn" onclick="assignWarehouse('${orderId}')">🏭 Assign Warehouse</button>`,
                'warehouse_assigned': `<button class="btn" onclick="pickOrder('${orderId}')">📦 Mark as Picked</button>`,
                'picking': `<button class="btn" onclick="packOrder('${orderId}')">📦 Mark as Packed</button>`,
                'packed': `<button class="btn" onclick="qualityCheck('${orderId}')">🔍 Quality Check</button>`,
                'quality_checked': `<button class="btn" onclick="shipOrder('${orderId}')">🚚 Ship Order</button>`
            };
            return actions[status] || '';
        }
        
        async function validateOrder(orderId) {
            // Fetch validation data
            const response = await fetch('/api/orders/' + orderId + '/validation-data');
            const data = await response.json();
            
            // Build decision UI
            let html = '<div class="order-card" style="background: #f8f9fa; max-width: 800px; margin: 0 auto;">';
            html += '<h3>🔍 Fraud & Validation Review</h3>';
            html += '<p style="color: #666; margin-bottom: 1rem;">Review the following information and decide whether to approve this order.</p>';
            
            // Order info
            html += '<div style="background: white; padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">';
            html += '<h4>Order Information</h4>';
            html += `<div><strong>Order ID:</strong> ${data.order.id}</div>`;
            html += `<div><strong>Total Amount:</strong> $${data.order.total.toFixed(2)}</div>`;
            html += `<div><strong>Shipping Address:</strong> ${data.order.shipping_address}</div>`;
            html += '</div>';
            
            // Customer info
            html += '<div style="background: white; padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">';
            html += '<h4>Customer Profile</h4>';
            html += `<div><strong>Name:</strong> ${data.customer.name}</div>`;
            html += `<div><strong>Email:</strong> ${data.customer.email}</div>`;
            html += `<div><strong>Account Age:</strong> ${data.customer.account_age_days} days</div>`;
            html += `<div><strong>Total Orders:</strong> ${data.customer.total_orders}</div>`;
            html += `<div><strong>Total Spent:</strong> $${data.customer.total_spent.toFixed(2)}</div>`;
            html += '</div>';
            
            // Risk factors
            html += '<div style="background: white; padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">';
            html += '<h4>Risk Analysis</h4>';
            data.risk_factors.forEach(risk => {
                const color = risk.severity === 'high' ? '#dc3545' : (risk.severity === 'medium' ? '#ffc107' : '#28a745');
                html += `<div style="padding: 0.5rem; margin: 0.5rem 0; border-left: 3px solid ${color}; background: #f8f9fa;">`;
                html += `<strong>${risk.factor}</strong> (${risk.severity})<br><small>${risk.description}</small>`;
                html += '</div>';
            });
            html += `<div style="margin-top: 1rem; padding: 1rem; background: ${data.fraud_score > 40 ? '#fff3cd' : '#d4edda'}; border-radius: 4px;">`;
            html += `<strong>Fraud Score:</strong> ${data.fraud_score}/100<br>`;
            html += `<strong>Recommendation:</strong> ${data.recommendation}`;
            html += '</div>';
            html += '</div>';
            
            // Decision buttons
            html += '<div style="display: flex; gap: 1rem; margin-top: 1rem;">';
            html += `<button class="btn" onclick="approveValidation('${orderId}')" style="flex: 1; background: #28a745;">✅ Approve Order</button>`;
            html += `<button class="btn" onclick="rejectValidation('${orderId}')" style="flex: 1; background: #dc3545;">❌ Reject Order</button>`;
            html += `<button class="btn" onclick="loadFulfillmentOrders()" style="background: #6c757d;">← Cancel</button>`;
            html += '</div>';
            html += '</div>';
            
            document.getElementById('fulfillment-orders-list').innerHTML = html;
        }
        
        async function approveValidation(orderId) {
            const messageDiv = document.getElementById('fulfillment-message');
            const response = await fetch('/api/orders/' + orderId + '/validate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({approved: true, notes: 'Order validated - approved after manual review'})
            });
            const data = await response.json();
            if (data.success) {
                messageDiv.innerHTML = '<div class="alert alert-success">✅ Order validated successfully</div>';
                setTimeout(() => { messageDiv.innerHTML = ''; loadFulfillmentOrders(); }, 1500);
            } else {
                messageDiv.innerHTML = '<div class="alert alert-error">Error: ' + data.error + '</div>';
            }
        }
        
        async function rejectValidation(orderId) {
            const reason = prompt('Enter rejection reason:');
            if (!reason) return;
            alert('Order rejected. In production, this would cancel the order and notify the customer.');
            loadFulfillmentOrders();
        }
        
        async function assignWarehouse(orderId) {
            console.log('assignWarehouse called with orderId:', orderId);
            try {
                // Get warehouse loads from control panel (if set)
                const warehouseLoads = sessionStorage.getItem('warehouse_loads');
                let url = '/api/warehouses/assignment-options?orderId=' + orderId;
                if (warehouseLoads) {
                    url += '&warehouseLoads=' + encodeURIComponent(warehouseLoads);
                }
                
                // Fetch warehouse assignment options
                const response = await fetch(url);
                console.log('Response status:', response.status, response.statusText);
                
                if (!response.ok) {
                    const text = await response.text();
                    console.error('Error response:', text);
                    alert('Error loading warehouse options: ' + response.status);
                    return;
                }
                
                const data = await response.json();
                console.log('Warehouse options received:', data);
                
                // Build decision UI
            let html = '<div class="order-card" style="background: #f8f9fa; max-width: 900px; margin: 0 auto;">';
            html += '<h3>🏭 Warehouse Assignment</h3>';
            html += '<p style="color: #666; margin-bottom: 1rem;">Select the optimal warehouse for this order based on distance, cost, and delivery time.</p>';
            
            // Order destination
            html += '<div style="background: white; padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">';
            html += '<h4>Delivery Destination</h4>';
            html += `<div><strong>Address:</strong> ${data.order.shipping_address}</div>`;
            html += `<div><strong>Coordinates:</strong> ${data.order.destination_lat}, ${data.order.destination_lng}</div>`;
            html += '</div>';
            
            // Warehouse comparison table
            html += '<div style="background: white; padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">';
            html += '<h4>Available Warehouses</h4>';
            html += '<table style="width: 100%; border-collapse: collapse;">';
            html += '<thead><tr style="background: #f8f9fa; border-bottom: 2px solid #dee2e6;">';
            html += '<th style="padding: 0.75rem; text-align: left;">Warehouse</th>';
            html += '<th style="padding: 0.75rem; text-align: center;">Distance</th>';
            html += '<th style="padding: 0.75rem; text-align: center;">Shipping Cost</th>';
            html += '<th style="padding: 0.75rem; text-align: center;">Delivery Time</th>';
            html += '<th style="padding: 0.75rem; text-align: center;">Score</th>';
            html += '<th style="padding: 0.75rem; text-align: center;">Action</th>';
            html += '</tr></thead><tbody>';
            
            data.warehouses.forEach(wh => {
                const scoreColor = wh.recommendation_score >= 80 ? '#28a745' : (wh.recommendation_score >= 60 ? '#ffc107' : '#dc3545');
                const isRecommended = wh.recommendation_score === Math.max(...data.warehouses.map(w => w.recommendation_score));
                html += `<tr style="border-bottom: 1px solid #dee2e6; ${isRecommended ? 'background: #d4edda;' : ''}">`;
                html += `<td style="padding: 0.75rem;"><strong>${wh.name}</strong><br><small>${wh.location}</small></td>`;
                html += `<td style="padding: 0.75rem; text-align: center;">${wh.distance_miles} mi</td>`;
                html += `<td style="padding: 0.75rem; text-align: center;">$${wh.shipping_cost.toFixed(2)}</td>`;
                html += `<td style="padding: 0.75rem; text-align: center;">${wh.estimated_delivery_days} days</td>`;
                html += `<td style="padding: 0.75rem; text-align: center;"><span style="color: ${scoreColor}; font-weight: bold;">${wh.recommendation_score}</span></td>`;
                html += `<td style="padding: 0.75rem; text-align: center;">`;
                html += `<button class="btn" onclick="confirmWarehouse('${orderId}', '${wh.id}')" style="padding: 0.25rem 0.75rem; ${isRecommended ? 'background: #28a745;' : ''}">`;
                html += `${isRecommended ? '⭐ Select' : 'Select'}`;
                html += `</button></td>`;
                html += '</tr>';
            });
            
            html += '</tbody></table>';
            html += '</div>';
            
            // Cancel button
            html += '<div style="margin-top: 1rem;">';
            html += `<button class="btn" onclick="loadFulfillmentOrders()" style="background: #6c757d;">← Cancel</button>`;
            html += '</div>';
            html += '</div>';
            
            document.getElementById('fulfillment-orders-list').innerHTML = html;
            } catch (error) {
                console.error('Error in assignWarehouse:', error);
                alert('Error loading warehouse options: ' + error.message);
            }
        }
        
        async function confirmWarehouse(orderId, warehouseId) {
            const messageDiv = document.getElementById('fulfillment-message');
            try {
                const response = await fetch('/api/orders/' + orderId + '/assign-warehouse', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({warehouse_id: warehouseId})
                });
                const data = await response.json();
                if (data.success) {
                    messageDiv.innerHTML = '<div class="alert alert-success">✅ Warehouse assigned: ' + warehouseId + '</div>';
                    setTimeout(() => { messageDiv.innerHTML = ''; loadFulfillmentOrders(); }, 1500);
                } else {
                    messageDiv.innerHTML = '<div class="alert alert-error">Error: ' + (data.error || 'Unknown error') + '</div>';
                }
            } catch (error) {
                console.error('Error assigning warehouse:', error);
                messageDiv.innerHTML = '<div class="alert alert-error">Error: ' + error.message + '</div>';
            }
        }
        
        async function pickOrder(orderId) {
            // Get picker statuses from sessionStorage
            const pickerStatuses = JSON.parse(sessionStorage.getItem('picker_statuses') || '{"picker-001": "Available", "picker-002": "Available", "picker-003": "On Break"}');
            
            // Fetch picking details with picker statuses
            const queryParams = new URLSearchParams();
            Object.keys(pickerStatuses).forEach(pickerId => {
                queryParams.append('pickerStatus[' + pickerId + ']', pickerStatuses[pickerId]);
            });
            
            const response = await fetch('/api/orders/' + orderId + '/picking-details?' + queryParams.toString());
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Picking details error:', response.status, errorText);
                alert('Error loading picking details: ' + response.status + '\n' + errorText);
                return;
            }
            
            const data = await response.json();
            console.log('Picking details data:', data);
            
            // Check if data is valid
            if (!data) {
                console.error('No data returned');
                alert('Error loading picking details: No data returned');
                return;
            }
            
            if (data.error) {
                console.error('API error:', data.error);
                alert('Error loading picking details: ' + data.error);
                return;
            }
            
            if (!data.items || !Array.isArray(data.items)) {
                console.error('Invalid items:', data.items);
                alert('Error loading picking details: Invalid items data');
                return;
            }
            
            if (!data.available_pickers || !Array.isArray(data.available_pickers)) {
                console.error('Invalid pickers:', data.available_pickers);
                alert('Error loading picking details: Invalid pickers data');
                return;
            }
            
            // Build decision UI
            let html = '<div class="order-card" style="background: #f8f9fa; max-width: 900px; margin: 0 auto;">';
            html += '<h3>📦 Order Picking</h3>';
            html += '<p style="color: #666; margin-bottom: 1rem;">Review item locations and assign a picker to collect the items.</p>';
            
            // Order items with locations
            html += '<div style="background: white; padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">';
            html += '<h4>Items to Pick</h4>';
            html += '<table style="width: 100%; border-collapse: collapse;">';
            html += '<thead><tr style="background: #f8f9fa; border-bottom: 2px solid #dee2e6;">';
            html += '<th style="padding: 0.75rem; text-align: left;">Product</th>';
            html += '<th style="padding: 0.75rem; text-align: center;">Quantity</th>';
            html += '<th style="padding: 0.75rem; text-align: left;">Location</th>';
            html += '<th style="padding: 0.75rem; text-align: center;">Est. Time</th>';
            html += '</tr></thead><tbody>';
            
            data.items.forEach(item => {
                html += `<tr style="border-bottom: 1px solid #dee2e6;">`;
                html += `<td style="padding: 0.75rem;"><strong>${item.name}</strong></td>`;
                html += `<td style="padding: 0.75rem; text-align: center;">${item.quantity}</td>`;
                html += `<td style="padding: 0.75rem;">${item.location}</td>`;
                html += `<td style="padding: 0.75rem; text-align: center;">${item.estimated_pick_time_minutes} min</td>`;
                html += '</tr>';
            });
            
            html += '</tbody></table>';
            html += `<div style="margin-top: 1rem; padding: 0.75rem; background: #e7f3ff; border-radius: 4px;">`;
            html += `<strong>Total Estimated Time:</strong> ${data.total_estimated_time_minutes} minutes`;
            html += '</div>';
            html += '</div>';
            
            // Available pickers
            html += '<div style="background: white; padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">';
            html += '<h4>Available Pickers</h4>';
            html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">';
            
            data.available_pickers.forEach(picker => {
                const statusColor = picker.status === 'Available' ? '#28a745' : '#ffc107';
                html += `<div style="padding: 1rem; border: 2px solid ${statusColor}; border-radius: 4px; background: ${picker.status === 'Available' ? '#d4edda' : '#fff3cd'};">`;
                html += `<strong>${picker.name}</strong><br>`;
                html += `<small>Efficiency: ${picker.efficiency_rating}/5 ⭐</small><br>`;
                html += `<small>Status: ${picker.status}</small><br>`;
                html += `<button class="btn" onclick="confirmPicker('${orderId}', '${picker.id}')" style="margin-top: 0.5rem; width: 100%; padding: 0.25rem;">Assign</button>`;
                html += '</div>';
            });
            
            html += '</div></div>';
            
            // Cancel button
            html += '<div style="margin-top: 1rem;">';
            html += `<button class="btn" onclick="loadFulfillmentOrders()" style="background: #6c757d;">← Cancel</button>`;
            html += '</div>';
            html += '</div>';
            
            document.getElementById('fulfillment-orders-list').innerHTML = html;
        }
        
        async function confirmPicker(orderId, pickerId) {
            const messageDiv = document.getElementById('fulfillment-message');
            const response = await fetch('/api/orders/' + orderId + '/pick', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({picker_id: pickerId, notes: 'Picker assigned: ' + pickerId})
            });
            const data = await response.json();
            if (data.success) {
                messageDiv.innerHTML = '<div class="alert alert-success">✅ Picker assigned - order marked as picked</div>';
                setTimeout(() => { messageDiv.innerHTML = ''; loadFulfillmentOrders(); }, 1500);
            } else {
                messageDiv.innerHTML = '<div class="alert alert-error">Error: ' + data.error + '</div>';
            }
        }
        
        async function packOrder(orderId) {
            // Fetch packing options
            const response = await fetch('/api/orders/' + orderId + '/packing-options');
            const data = await response.json();
            
            // Build decision UI
            let html = '<div class="order-card" style="background: #f8f9fa; max-width: 900px; margin: 0 auto;">';
            html += '<h3>📦 Packing Selection</h3>';
            html += '<p style="color: #666; margin-bottom: 1rem;">Choose the most appropriate box size for this order to minimize waste and shipping costs.</p>';
            
            // Order dimensions
            html += '<div style="background: white; padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">';
            html += '<h4>Order Requirements</h4>';
            html += `<div><strong>Total Volume:</strong> ${data.order.total_volume_cubic_inches.toFixed(1)} in³</div>`;
            html += `<div><strong>Total Weight:</strong> ${data.order.total_weight_lbs.toFixed(2)} lbs</div>`;
            html += `<div><strong>Dimensions:</strong> ${data.order.max_length}" × ${data.order.max_width}" × ${data.order.total_height}"</div>`;
            html += '</div>';
            
            // Box options
            html += '<div style="background: white; padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">';
            html += '<h4>Available Box Options</h4>';
            html += '<table style="width: 100%; border-collapse: collapse;">';
            html += '<thead><tr style="background: #f8f9fa; border-bottom: 2px solid #dee2e6;">';
            html += '<th style="padding: 0.75rem; text-align: left;">Box Type</th>';
            html += '<th style="padding: 0.75rem; text-align: center;">Dimensions</th>';
            html += '<th style="padding: 0.75rem; text-align: center;">Fit</th>';
            html += '<th style="padding: 0.75rem; text-align: center;">Waste</th>';
            html += '<th style="padding: 0.75rem; text-align: center;">Cost</th>';
            html += '<th style="padding: 0.75rem; text-align: center;">Action</th>';
            html += '</tr></thead><tbody>';
            
            data.box_options.forEach(box => {
                const fitColor = box.fits ? '#28a745' : '#dc3545';
                const wasteColor = box.waste_percentage < 20 ? '#28a745' : (box.waste_percentage < 40 ? '#ffc107' : '#dc3545');
                const isRecommended = box.recommended;
                html += `<tr style="border-bottom: 1px solid #dee2e6; ${isRecommended ? 'background: #d4edda;' : ''}">`;
                html += `<td style="padding: 0.75rem;"><strong>${box.name}</strong></td>`;
                html += `<td style="padding: 0.75rem; text-align: center;">${box.dimensions}</td>`;
                html += `<td style="padding: 0.75rem; text-align: center;"><span style="color: ${fitColor};">${box.fits ? '✓ Yes' : '✗ No'}</span></td>`;
                html += `<td style="padding: 0.75rem; text-align: center;"><span style="color: ${wasteColor};">${box.waste_percentage.toFixed(1)}%</span></td>`;
                html += `<td style="padding: 0.75rem; text-align: center;">$${box.cost.toFixed(2)}</td>`;
                html += `<td style="padding: 0.75rem; text-align: center;">`;
                if (box.fits) {
                    html += `<button class="btn" onclick="confirmBox('${orderId}', '${box.id}')" style="padding: 0.25rem 0.75rem; ${isRecommended ? 'background: #28a745;' : ''}">`;
                    html += `${isRecommended ? '⭐ Select' : 'Select'}`;
                    html += `</button>`;
                } else {
                    html += '<span style="color: #999;">Too small</span>';
                }
                html += `</td>`;
                html += '</tr>';
            });
            
            html += '</tbody></table>';
            html += '</div>';
            
            // Cancel button
            html += '<div style="margin-top: 1rem;">';
            html += `<button class="btn" onclick="loadFulfillmentOrders()" style="background: #6c757d;">← Cancel</button>`;
            html += '</div>';
            html += '</div>';
            
            document.getElementById('fulfillment-orders-list').innerHTML = html;
        }
        
        async function confirmBox(orderId, boxId) {
            const messageDiv = document.getElementById('fulfillment-message');
            const response = await fetch('/api/orders/' + orderId + '/pack', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({box_id: boxId, notes: 'Packed in box: ' + boxId})
            });
            const data = await response.json();
            if (data.success) {
                messageDiv.innerHTML = '<div class="alert alert-success">✅ Order packed successfully</div>';
                setTimeout(() => { messageDiv.innerHTML = ''; loadFulfillmentOrders(); }, 1500);
            } else {
                messageDiv.innerHTML = '<div class="alert alert-error">Error: ' + data.error + '</div>';
            }
        }
        
        async function qualityCheck(orderId) {
            // Read QC settings from control panel
            const qcStrictness = sessionStorage.getItem('qc-strictness') || 'standard';
            const qcThreshold = sessionStorage.getItem('qc-threshold') || '95';
            
            // Fetch quality checklist with QC settings
            const response = await fetch('/api/orders/' + orderId + '/quality-checklist?qcStrictness=' + qcStrictness + '&qcThreshold=' + qcThreshold);
            const data = await response.json();
            
            // Build decision UI
            let html = '<div class="order-card" style="background: #f8f9fa; max-width: 800px; margin: 0 auto;">';
            html += '<h3>✅ Quality Control Inspection</h3>';
            html += '<p style="color: #666; margin-bottom: 1rem;">Complete all inspection items before approving this order for shipment.</p>';
            
            // Order info
            html += '<div style="background: white; padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">';
            html += '<h4>Order Information</h4>';
            html += `<div><strong>Order ID:</strong> ${data.order.id}</div>`;
            html += `<div><strong>Customer:</strong> ${data.order.customer_name}</div>`;
            html += `<div><strong>Items:</strong> ${data.order.item_count}</div>`;
            html += '</div>';
            
            // Checklist
            html += '<div style="background: white; padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">';
            html += '<h4>Inspection Checklist</h4>';
            html += '<form id="qc-form">';
            
            data.checklist.forEach((item, index) => {
                const criticalBadge = item.critical ? '<span style="color: #dc3545; font-weight: bold; margin-left: 0.5rem;">[CRITICAL]</span>' : '';
                html += `<div style="padding: 0.75rem; margin: 0.5rem 0; background: #f8f9fa; border-radius: 4px;">`;
                html += `<label style="display: flex; align-items: start; cursor: pointer;">`;
                html += `<input type="checkbox" id="qc-${index}" style="margin-right: 0.75rem; margin-top: 0.25rem; width: 18px; height: 18px;" ${item.critical ? 'required' : ''}>`;
                html += `<div><strong>${item.item}</strong>${criticalBadge}<br><small style="color: #666;">${item.description}</small></div>`;
                html += `</label>`;
                html += '</div>';
            });
            
            html += '</form>';
            html += '<div style="margin-top: 1rem; padding: 0.75rem; background: #fff3cd; border-radius: 4px; border-left: 3px solid #ffc107;">';
            html += '<strong>Note:</strong> All items marked as CRITICAL must be checked before approval.';
            html += '</div>';
            html += '</div>';
            
            // Action buttons
            html += '<div style="display: flex; gap: 1rem; margin-top: 1rem;">';
            html += `<button class="btn" onclick="approveQC('${orderId}')" style="flex: 1; background: #28a745;">✅ Pass QC</button>`;
            html += `<button class="btn" onclick="failQC('${orderId}')" style="flex: 1; background: #dc3545;">❌ Fail QC</button>`;
            html += `<button class="btn" onclick="loadFulfillmentOrders()" style="background: #6c757d;">← Cancel</button>`;
            html += '</div>';
            html += '</div>';
            
            document.getElementById('fulfillment-orders-list').innerHTML = html;
        }
        
        async function approveQC(orderId) {
            const form = document.getElementById('qc-form');
            if (!form.checkValidity()) {
                alert('Please complete all critical inspection items before approving.');
                return;
            }
            
            const messageDiv = document.getElementById('fulfillment-message');
            const response = await fetch('/api/orders/' + orderId + '/quality-check', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({passed: true, notes: 'All quality checks passed'})
            });
            const data = await response.json();
            if (data.success) {
                messageDiv.innerHTML = '<div class="alert alert-success">✅ Quality check passed</div>';
                setTimeout(() => { messageDiv.innerHTML = ''; loadFulfillmentOrders(); }, 1500);
            } else {
                messageDiv.innerHTML = '<div class="alert alert-error">Error: ' + data.error + '</div>';
            }
        }
        
        async function failQC(orderId) {
            const reason = prompt('Enter reason for QC failure:');
            if (!reason) return;
            
            const messageDiv = document.getElementById('fulfillment-message');
            const response = await fetch('/api/orders/' + orderId + '/quality-check', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({passed: false, notes: 'QC Failed: ' + reason})
            });
            const data = await response.json();
            if (data.success) {
                messageDiv.innerHTML = '<div class="alert alert-error">❌ Order failed QC - returned to packing</div>';
                setTimeout(() => { messageDiv.innerHTML = ''; loadFulfillmentOrders(); }, 2000);
            } else {
                messageDiv.innerHTML = '<div class="alert alert-error">Error: ' + data.error + '</div>';
            }
        }
        
        async function shipOrder(orderId) {
            console.log('shipOrder called with orderId:', orderId);
            try {
                // Get shipping settings from control panel (sessionStorage)
                const shippingMultiplier = sessionStorage.getItem('shipping-multiplier') || '1.0';
                const carrierReliability = sessionStorage.getItem('carrier-reliability') || 'normal';
                const shippingPriority = sessionStorage.getItem('shipping-priority') || 'balanced';
                
                // Fetch shipping options with control panel settings
                const queryParams = new URLSearchParams({
                    orderId: orderId,
                    shippingMultiplier: shippingMultiplier,
                    carrierReliability: carrierReliability,
                    shippingPriority: shippingPriority
                });
                
                const response = await fetch('/api/carriers/shipping-options?' + queryParams.toString());
                
                if (!response.ok) {
                    alert('Error loading shipping options: ' + response.status);
                    return;
                }
                
                const data = await response.json();
                console.log('Shipping options received:', data);
            
            // Build decision UI
            let html = '<div class="order-card" style="background: #f8f9fa; max-width: 1000px; margin: 0 auto;">';
            html += '<h3>🚚 Shipping Carrier Selection</h3>';
            html += '<p style="color: #666; margin-bottom: 1rem;">Choose the best carrier and service level for this shipment.</p>';
            
            // Order info
            html += '<div style="background: white; padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">';
            html += '<h4>Shipment Details</h4>';
            html += `<div><strong>Destination:</strong> ${data.order.shipping_address}</div>`;
            html += `<div><strong>Weight:</strong> ${data.order.total_weight_lbs.toFixed(2)} lbs</div>`;
            html += `<div><strong>Dimensions:</strong> ${data.order.package_dimensions}</div>`;
            html += '</div>';
            
            // Carrier options grouped by carrier
            const carriers = {};
            data.options.forEach(opt => {
                if (!carriers[opt.carrier]) carriers[opt.carrier] = [];
                carriers[opt.carrier].push(opt);
            });
            
            html += '<div style="background: white; padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">';
            html += '<h4>Available Shipping Options</h4>';
            
            Object.keys(carriers).forEach(carrierName => {
                html += `<h5 style="margin-top: 1rem; color: #333;">${carrierName}</h5>`;
                html += '<table style="width: 100%; border-collapse: collapse; margin-bottom: 1rem;">';
                html += '<thead><tr style="background: #f8f9fa; border-bottom: 2px solid #dee2e6;">';
                html += '<th style="padding: 0.75rem; text-align: left;">Service Level</th>';
                html += '<th style="padding: 0.75rem; text-align: center;">Delivery Time</th>';
                html += '<th style="padding: 0.75rem; text-align: center;">Rate</th>';
                html += '<th style="padding: 0.75rem; text-align: center;">Reliability</th>';
                html += '<th style="padding: 0.75rem; text-align: center;">Action</th>';
                html += '</tr></thead><tbody>';
                
                carriers[carrierName].forEach(opt => {
                    const isRecommended = opt.recommended;
                    html += `<tr style="border-bottom: 1px solid #dee2e6; ${isRecommended ? 'background: #d4edda;' : ''}">`;
                    html += `<td style="padding: 0.75rem;"><strong>${opt.service_level}</strong></td>`;
                    html += `<td style="padding: 0.75rem; text-align: center;">${opt.estimated_delivery_days} days</td>`;
                    html += `<td style="padding: 0.75rem; text-align: center;">$${opt.rate.toFixed(2)}</td>`;
                    html += `<td style="padding: 0.75rem; text-align: center;">${opt.reliability_score}%</td>`;
                    html += `<td style="padding: 0.75rem; text-align: center;">`;
                    html += `<button class="btn" onclick="confirmShipping('${orderId}', '${opt.carrier}', '${opt.service_level}')" style="padding: 0.25rem 0.75rem; ${isRecommended ? 'background: #28a745;' : ''}">`;
                    html += `${isRecommended ? '⭐ Select' : 'Select'}`;
                    html += `</button></td>`;
                    html += '</tr>';
                });
                
                html += '</tbody></table>';
            });
            
            html += '</div>';
            
            // Cancel button
            html += '<div style="margin-top: 1rem;">';
            html += `<button class="btn" onclick="loadFulfillmentOrders()" style="background: #6c757d;">← Cancel</button>`;
            html += '</div>';
            html += '</div>';
            
            document.getElementById('fulfillment-orders-list').innerHTML = html;
            } catch (error) {
                console.error('Error in shipOrder:', error);
                alert('Error loading shipping options: ' + error.message);
            }
        }
        
        async function confirmShipping(orderId, carrier, serviceLevel) {
            const messageDiv = document.getElementById('fulfillment-message');
            try {
                const response = await fetch('/api/orders/' + orderId + '/ship', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({carrier: carrier, service_level: serviceLevel})
                });
                const data = await response.json();
                if (data.success) {
                    messageDiv.innerHTML = '<div class="alert alert-success">✅ Order shipped! Tracking: ' + data.tracking_number + '</div>';
                    setTimeout(() => { messageDiv.innerHTML = ''; loadFulfillmentOrders(); }, 2000);
                } else {
                    messageDiv.innerHTML = '<div class="alert alert-error">Error: ' + (data.error || 'Unknown error') + '</div>';
                }
            } catch (error) {
                console.error('Error shipping order:', error);
                messageDiv.innerHTML = '<div class="alert alert-error">Error: ' + error.message + '</div>';
            }
        }
        
        async function viewOrderHistory(orderId) {
            const response = await fetch('/api/orders/' + orderId + '/history');
            const data = await response.json();
            
            let historyHtml = '<div class="order-card" style="background: #f8f9fa;"><h3>Order Status History</h3>';
            data.history.forEach(h => {
                historyHtml += `
                    <div style="padding: 0.75rem; margin: 0.5rem 0; background: white; border-left: 3px solid #ff9900; border-radius: 4px;">
                        <strong>${h.status}</strong> - ${new Date(h.created_at).toLocaleString()}<br>
                        <small>By: ${h.changed_by}</small><br>
                        ${h.notes ? '<em>' + h.notes + '</em>' : ''}
                    </div>
                `;
            });
            historyHtml += '<button class="btn" onclick="loadFulfillmentOrders()" style="margin-top: 1rem;">← Back to Orders</button></div>';
            
            document.getElementById('fulfillment-orders-list').innerHTML = historyHtml;
        }
        
        async function loadProducts() {
            const response = await fetch('/api/products');
            const data = await response.json();
            const productsGrid = document.getElementById('products-grid');
            if (productsGrid) {
                productsGrid.innerHTML = data.products.map(product => `
                <div class="product-card">
                    <h3>${product.product_name}</h3>
                    <p>${product.description}</p>
                    <div class="price">$${product.price}</div>
                    <div class="stock">Stock: ${product.stock_quantity}</div>
                    <button class="btn" onclick="buyProduct('${product.product_id}')" ${product.stock_quantity === 0 ? 'disabled' : ''}>
                        ${product.stock_quantity === 0 ? 'Out of Stock' : 'Buy Now'}
                    </button>
                </div>
            `).join('');
            }
        }
        
        async function buyProduct(productId) {
            // Show address form modal
            const modal = document.createElement('div');
            modal.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000;';
            modal.innerHTML = `
                <div style="background: white; border-radius: 8px; padding: 2rem; max-width: 500px; width: 90%;">
                    <h3 style="margin-bottom: 1rem;">Enter Shipping Address</h3>
                    <div class="form-group">
                        <label>Street Address</label>
                        <input type="text" id="street" placeholder="123 Main St" required>
                    </div>
                    <div class="form-group">
                        <label>City</label>
                        <input type="text" id="city" placeholder="Seattle" required>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                        <div class="form-group">
                            <label>State</label>
                            <input type="text" id="state" placeholder="WA" maxlength="2" required>
                        </div>
                        <div class="form-group">
                            <label>ZIP Code</label>
                            <input type="text" id="zip" placeholder="98101" maxlength="5" required>
                        </div>
                    </div>
                    <div style="display: flex; gap: 1rem; margin-top: 1.5rem;">
                        <button class="btn" onclick="confirmPurchase('${productId}')" style="flex: 1;">Place Order</button>
                        <button class="btn" onclick="this.closest('div[style*=fixed]').remove()" style="flex: 1; background: #6c757d;">Cancel</button>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        }
        
        async function confirmPurchase(productId) {
            const street = document.getElementById('street').value;
            const city = document.getElementById('city').value;
            const state = document.getElementById('state').value.toUpperCase();
            const zip = document.getElementById('zip').value;
            
            if (!street || !city || !state || !zip) {
                alert('Please fill in all address fields');
                return;
            }
            
            const shippingAddress = `${street}, ${city}, ${state} ${zip}`;
            
            const response = await fetch('/api/orders', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    payment_method: 'credit_card',
                    shipping_address: shippingAddress,
                    items: [{product_id: productId, quantity: 1}]
                })
            });
            const data = await response.json();
            
            // Close modal
            document.querySelector('div[style*="position: fixed"]').remove();
            
            if (data.success) {
                alert('Order placed! ID: ' + data.order_id + '\nShipping to: ' + shippingAddress);
                loadProducts();
            } else {
                alert('Error: ' + data.error);
            }
        }
        
        async function loadOrders() {
            const response = await fetch('/api/orders/me');
            const data = await response.json();
            const list = document.getElementById('orders-list');
            if (data.orders.length === 0) {
                list.innerHTML = '<p>No orders found.</p>';
                return;
            }
            list.innerHTML = data.orders.map(order => `
                <div class="order-card">
                    <div class="order-header">
                        <div>
                            <strong>Order ID:</strong> ${order.id}<br>
                            <strong>Date:</strong> ${new Date(order.created_at).toLocaleDateString()}<br>
                            ${order.shipping_address ? '<strong>Shipping to:</strong> ' + order.shipping_address + '<br>' : ''}
                            ${order.tracking_number ? '<strong>Tracking:</strong> ' + order.tracking_number + ' (' + order.carrier + ')<br>' : ''}
                        </div>
                        <div><span class="status-badge status-${order.status}">${order.status}</span></div>
                    </div>
                    <div><strong>Total:</strong> $${parseFloat(order.total_amount).toFixed(2)}</div>
                    ${order.status === 'shipped' ? '<button class="btn" style="margin-top: 1rem;" onclick="confirmDelivery(\'' + order.id + '\')">📦 Confirm Delivery</button>' : ''}
                </div>
            `).join('');
        }
        
        async function confirmDelivery(orderId) {
            if (!confirm('Confirm that you have received this package?')) {
                return;
            }
            
            const response = await fetch('/api/orders/' + orderId + '/confirm-delivery', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({})
            });
            const data = await response.json();
            
            if (data.success) {
                alert('✅ Delivery confirmed! Thank you for your order.');
                loadOrders();
            } else {
                alert('Error: ' + data.error);
            }
        }
        
        async function processReturn() {
            const orderId = document.getElementById('return-order-id').value;
            const reason = document.getElementById('return-reason').value;
            const messageDiv = document.getElementById('return-message');
            if (!orderId || !reason) {
                messageDiv.innerHTML = '<div class="alert alert-error">Please fill in all fields</div>';
                return;
            }
            const response = await fetch('/api/returns', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({order_id: orderId, reason: reason})
            });
            const data = await response.json();
            if (data.success) {
                messageDiv.innerHTML = '<div class="alert alert-success"><strong>Return Request Submitted</strong><br>Return ID: ' + data.return_id + '<br><br>' + data.message + '<br><br><em>⚠️ This manual review process is a pain point in the monolith that will be automated with AI agents in the microservices architecture.</em></div>';
                document.getElementById('return-order-id').value = '';
                document.getElementById('return-reason').value = '';
            } else {
                messageDiv.innerHTML = '<div class="alert alert-error">Error: ' + data.error + '</div>';
            }
        }
        
        async function loadPendingReturns() {
            const response = await fetch('/api/admin/pending-returns');
            const data = await response.json();
            const list = document.getElementById('pending-returns-list');
            if (data.returns.length === 0) {
                list.innerHTML = '<div class="order-card"><p>No pending returns to review.</p></div>';
                return;
            }
            list.innerHTML = data.returns.map(ret => `
                <div class="order-card">
                    <div class="order-header">
                        <div>
                            <strong>Return ID:</strong> ${ret.id}<br>
                            <strong>Order ID:</strong> ${ret.order_id}<br>
                            <strong>Customer:</strong> ${ret.customer_name} (${ret.customer_email})<br>
                            <strong>Submitted:</strong> ${new Date(ret.created_at).toLocaleString()}
                        </div>
                        <div><span class="status-badge" style="background: #fff3cd; color: #856404;">${ret.status}</span></div>
                    </div>
                    <div style="margin: 1rem 0; padding: 1rem; background: #f8f9fa; border-radius: 4px;">
                        <strong>Return Reason:</strong><br>
                        ${ret.reason}
                    </div>
                    <div style="margin-bottom: 1rem;">
                        <strong>Refund Amount:</strong> $${parseFloat(ret.total_amount).toFixed(2)}
                    </div>
                    <div style="display: flex; gap: 1rem;">
                        <button class="btn" onclick="approveReturn('${ret.id}')">✅ Approve Return</button>
                        <button class="btn" style="background: #dc3545;" onclick="alert('Reject functionality not implemented in demo')">❌ Reject</button>
                    </div>
                </div>
            `).join('');
        }
        
        async function approveReturn(returnId) {
            const messageDiv = document.getElementById('admin-message');
            const response = await fetch('/api/admin/approve-return', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({return_id: returnId})
            });
            const data = await response.json();
            if (data.success) {
                messageDiv.innerHTML = '<div class="alert alert-success">✅ ' + data.message + '</div>';
                setTimeout(() => { messageDiv.innerHTML = ''; loadPendingReturns(); }, 2000);
            } else {
                messageDiv.innerHTML = '<div class="alert alert-error">Error: ' + data.error + '</div>';
            }
        }
        
        // AI Control Panel Functions
        async function updateWarehouseLoads() {
            const seattleLoad = document.getElementById('wh-seattle-load').value;
            const portlandLoad = document.getElementById('wh-portland-load').value;
            const sfLoad = document.getElementById('wh-sf-load').value;
            
            // Store in session storage for now (could be persisted to DB)
            sessionStorage.setItem('warehouse_loads', JSON.stringify({
                'Seattle Warehouse': parseInt(seattleLoad),
                'Portland Warehouse': parseInt(portlandLoad),
                'San Francisco Warehouse': parseInt(sfLoad)
            }));
            
            alert('✅ Warehouse load settings updated!\n\nThese will affect the next warehouse assignment decision.');
            loadConfigSummary();
        }
        
        async function updatePickerStatuses() {
            const pickerStatuses = {
                'picker-001': document.getElementById('picker-mike').value,
                'picker-002': document.getElementById('picker-sarah').value,
                'picker-003': document.getElementById('picker-david').value
            };
            
            // Store in session storage
            sessionStorage.setItem('picker_statuses', JSON.stringify(pickerStatuses));
            loadConfigSummary();
        }
        
        async function updateShippingSettings() {
            const shippingMultiplier = document.getElementById('shipping-multiplier').value;
            const carrierReliability = document.getElementById('carrier-reliability').value;
            const shippingPriority = document.getElementById('shipping-priority').value;
            
            // Store in session storage
            sessionStorage.setItem('shipping-multiplier', shippingMultiplier);
            sessionStorage.setItem('carrier-reliability', carrierReliability);
            sessionStorage.setItem('shipping-priority', shippingPriority);
            
            loadConfigSummary();
        }
        
        async function updateQCSettings() {
            const qcStrictness = document.getElementById('qc-strictness').value;
            const qcThreshold = document.getElementById('qc-threshold').value;
            
            // Store in session storage
            sessionStorage.setItem('qc-strictness', qcStrictness);
            sessionStorage.setItem('qc-threshold', qcThreshold);
            
            loadConfigSummary();
        }
        
        async function loadConfigSummary() {
            const summaryDiv = document.getElementById('config-summary');
            
            // Get all current settings
            const warehouseLoads = JSON.parse(sessionStorage.getItem('warehouse_loads') || '{"Seattle Warehouse": 0, "Portland Warehouse": 0, "San Francisco Warehouse": 0}');
            const pickerStatuses = {
                'Mike Johnson': document.getElementById('picker-mike').value,
                'Sarah Chen': document.getElementById('picker-sarah').value,
                'David Martinez': document.getElementById('picker-david').value
            };
            const shippingMultiplier = document.getElementById('shipping-multiplier').value;
            const carrierReliability = document.getElementById('carrier-reliability').value;
            const shippingPriority = document.getElementById('shipping-priority').value;
            const qcStrictness = document.getElementById('qc-strictness').value;
            const qcThreshold = document.getElementById('qc-threshold').value;
            
            // Build summary text
            let summary = '🏭 WAREHOUSE CONDITIONS:\n';
            summary += `  Seattle: ${warehouseLoads['Seattle Warehouse']}% capacity\n`;
            summary += `  Portland: ${warehouseLoads['Portland Warehouse']}% capacity\n`;
            summary += `  San Francisco: ${warehouseLoads['San Francisco Warehouse']}% capacity\n\n`;
            
            summary += '👷 PICKER AVAILABILITY:\n';
            summary += `  Mike Johnson: ${pickerStatuses['Mike Johnson']}\n`;
            summary += `  Sarah Chen: ${pickerStatuses['Sarah Chen']}\n`;
            summary += `  David Martinez: ${pickerStatuses['David Martinez']}\n\n`;
            
            summary += '📦 SHIPPING CONFIGURATION:\n';
            summary += `  Cost Multiplier: ${shippingMultiplier}x\n`;
            summary += `  Carrier Reliability: ${carrierReliability}\n`;
            summary += `  Priority: ${shippingPriority}\n\n`;
            
            summary += '✅ QUALITY STANDARDS:\n';
            summary += `  Inspection Level: ${qcStrictness}\n`;
            summary += `  Auto-Pass Threshold: ${qcThreshold}%\n\n`;
            
            summary += '💡 IMPACT ON AI DECISIONS:\n';
            summary += '  • Warehouse assignment will favor less loaded warehouses\n';
            summary += '  • Only available pickers will be assigned to orders\n';
            summary += '  • Shipping recommendations adjust based on priority setting\n';
            summary += '  • Quality checks adapt to strictness level\n';
            
            summaryDiv.textContent = summary;
        }
        
        // User Management Functions
        async function loadUsers() {
            const response = await fetch('/api/admin/users');
            const data = await response.json();
            const list = document.getElementById('users-list');
            
            if (data.users.length === 0) {
                list.innerHTML = '<div class="order-card"><p>No users found.</p></div>';
                return;
            }
            
            list.innerHTML = data.users.map(user => `
                <div class="order-card">
                    <div class="order-header">
                        <div>
                            <strong>Username:</strong> ${user.username}<br>
                            <strong>Name:</strong> ${user.name}<br>
                            <strong>Email:</strong> ${user.email}<br>
                            <strong>Created:</strong> ${new Date(user.created_at).toLocaleDateString()}
                        </div>
                        <div>
                            <span class="status-badge" style="background: ${user.role === 'admin' ? '#ff9900' : '#d1ecf1'}; color: ${user.role === 'admin' ? 'white' : '#0c5460'};">
                                ${user.role === 'admin' ? '👑 Admin' : '👤 Customer'}
                            </span>
                        </div>
                    </div>
                    <div style="display: flex; gap: 0.5rem; margin-top: 1rem;">
                        <button class="btn" onclick="editUser('${user.id}')" style="background: #2196F3;">✏️ Edit</button>
                        <button class="btn" onclick="deleteUser('${user.id}', '${user.username}')" style="background: #dc3545;">🗑️ Delete</button>
                    </div>
                </div>
            `).join('');
        }
        
        function showCreateUserForm() {
            document.getElementById('user-form-title').textContent = 'Create New User';
            document.getElementById('edit-user-id').value = '';
            document.getElementById('user-username').value = '';
            document.getElementById('user-username').disabled = false;
            document.getElementById('user-name').value = '';
            document.getElementById('user-email').value = '';
            document.getElementById('user-password').value = '';
            document.getElementById('user-password').required = true;
            document.getElementById('password-optional').textContent = '';
            document.getElementById('user-role').value = 'customer';
            document.getElementById('user-message').innerHTML = '';
            document.getElementById('user-form').style.display = 'block';
        }
        
        async function editUser(userId) {
            const response = await fetch('/api/admin/users');
            const data = await response.json();
            const user = data.users.find(u => u.id === userId);
            
            if (!user) {
                alert('User not found');
                return;
            }
            
            document.getElementById('user-form-title').textContent = 'Edit User';
            document.getElementById('edit-user-id').value = user.id;
            document.getElementById('user-username').value = user.username;
            document.getElementById('user-username').disabled = true;
            document.getElementById('user-name').value = user.name;
            document.getElementById('user-email').value = user.email;
            document.getElementById('user-password').value = '';
            document.getElementById('user-password').required = false;
            document.getElementById('password-optional').textContent = '(leave blank to keep current)';
            document.getElementById('user-role').value = user.role;
            document.getElementById('user-message').innerHTML = '';
            document.getElementById('user-form').style.display = 'block';
        }
        
        async function saveUser() {
            const userId = document.getElementById('edit-user-id').value;
            const username = document.getElementById('user-username').value;
            const name = document.getElementById('user-name').value;
            const email = document.getElementById('user-email').value;
            const password = document.getElementById('user-password').value;
            const role = document.getElementById('user-role').value;
            const messageDiv = document.getElementById('user-message');
            
            if (!username || !name || !email || !role) {
                messageDiv.innerHTML = '<div class="alert alert-error">Please fill in all required fields</div>';
                return;
            }
            
            if (!userId && !password) {
                messageDiv.innerHTML = '<div class="alert alert-error">Password is required for new users</div>';
                return;
            }
            
            const payload = { name, email, role };
            if (password) payload.password = password;
            if (!userId) payload.username = username;
            
            try {
                const url = userId ? `/api/admin/users/${userId}` : '/api/admin/users';
                const method = userId ? 'PUT' : 'POST';
                
                const response = await fetch(url, {
                    method: method,
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    messageDiv.innerHTML = '<div class="alert alert-success">✅ ' + data.message + '</div>';
                    setTimeout(() => {
                        cancelUserForm();
                        loadUsers();
                    }, 1500);
                } else {
                    messageDiv.innerHTML = '<div class="alert alert-error">Error: ' + data.error + '</div>';
                }
            } catch (error) {
                messageDiv.innerHTML = '<div class="alert alert-error">Error: ' + error.message + '</div>';
            }
        }
        
        async function deleteUser(userId, username) {
            if (!confirm(`Are you sure you want to delete user "${username}"?\n\nThis action cannot be undone.`)) {
                return;
            }
            
            try {
                const response = await fetch(`/api/admin/users/${userId}`, {
                    method: 'DELETE'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert('✅ ' + data.message);
                    loadUsers();
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }
        
        function cancelUserForm() {
            document.getElementById('user-form').style.display = 'none';
            document.getElementById('user-message').innerHTML = '';
        }
        
        // Initialize control panel on load
        if (document.getElementById('config-summary')) {
            loadConfigSummary();
        }
        
        // Initialize picker statuses in sessionStorage if not already set
        if (!sessionStorage.getItem('picker_statuses')) {
            sessionStorage.setItem('picker_statuses', JSON.stringify({
                'picker-001': 'Available',
                'picker-002': 'Available',
                'picker-003': 'On Break'
            }));
        }
        
        // Load picker statuses into dropdowns from sessionStorage
        const savedPickerStatuses = JSON.parse(sessionStorage.getItem('picker_statuses') || '{}');
        if (savedPickerStatuses['picker-001']) document.getElementById('picker-mike').value = savedPickerStatuses['picker-001'];
        if (savedPickerStatuses['picker-002']) document.getElementById('picker-sarah').value = savedPickerStatuses['picker-002'];
        if (savedPickerStatuses['picker-003']) document.getElementById('picker-david').value = savedPickerStatuses['picker-003'];
        
        // Load shipping settings from sessionStorage
        const savedShippingMultiplier = sessionStorage.getItem('shipping-multiplier');
        const savedCarrierReliability = sessionStorage.getItem('carrier-reliability');
        const savedShippingPriority = sessionStorage.getItem('shipping-priority');
        if (savedShippingMultiplier) {
            document.getElementById('shipping-multiplier').value = savedShippingMultiplier;
            document.getElementById('shipping-mult-val').textContent = savedShippingMultiplier + 'x';
        }
        if (savedCarrierReliability) document.getElementById('carrier-reliability').value = savedCarrierReliability;
        if (savedShippingPriority) document.getElementById('shipping-priority').value = savedShippingPriority;
        
        // Load QC settings from sessionStorage
        const savedQCStrictness = sessionStorage.getItem('qc-strictness');
        const savedQCThreshold = sessionStorage.getItem('qc-threshold');
        if (savedQCStrictness) document.getElementById('qc-strictness').value = savedQCStrictness;
        if (savedQCThreshold) {
            document.getElementById('qc-threshold').value = savedQCThreshold;
            document.getElementById('qc-threshold-val').textContent = savedQCThreshold + '%';
        }
        
        loadProducts();
    </script>
</body>
</html>
