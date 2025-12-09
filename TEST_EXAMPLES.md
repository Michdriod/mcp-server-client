# Comprehensive Test Examples for Database Query Assistant

## Performance Metrics (After Optimization)
- **Query Only**: ~6-9 seconds
- **Query + Chart**: ~8-12 seconds  
- **Speed Improvement**: 47% faster than initial version
- **Chart File Size**: Reduced by 60-70%

## Database Contents
- **5 customers**: John Doe, Jane Smith, Bob Johnson, Alice Williams, Charlie Brown
- **8 orders**: 6 completed, 2 pending
- **8 products**: Electronics (Laptop, Mouse, Keyboard, Monitor), Furniture (Desk Chair, Desk Lamp), Stationery (Notebook, Pen Set)
- **11 order items**: Various product purchases

---

## 1. Basic Queries (Counting & Listing)

### Customer Queries
```bash
python client/cli.py query "How many customers do we have?"
python client/cli.py query "Show me all customers with their email addresses"
python client/cli.py query "List all customers sorted by name"
```

### Product Queries
```bash
python client/cli.py query "Show me all products with their categories and prices"
python client/cli.py query "How many products do we have in each category?"
python client/cli.py query "What are the top 3 most expensive products?"
python client/cli.py query "Show me all electronics products"
python client/cli.py query "Which products cost less than $50?"
```

### Order Queries
```bash
python client/cli.py query "How many orders do we have so far?"
python client/cli.py query "Show me all order statuses and their counts"
python client/cli.py query "Are there any pending orders?"
python client/cli.py query "List all completed orders"
```

---

## 2. Complex JOIN Queries (Multi-Table)

### Customer Order Analysis
```bash
python client/cli.py query "Which customers have placed orders? Show their names and order counts"
python client/cli.py query "Show me all orders with customer names and order dates"
python client/cli.py query "Which customer has placed the most orders?"
python client/cli.py query "List customers who have never placed an order"
```

### Product-Customer Analysis
```bash
python client/cli.py query "How many customers ordered a keyboard?"
python client/cli.py query "Which customers have ordered keyboards? Show their names"
python client/cli.py query "Show me all customers who bought electronics products"
python client/cli.py query "Which products has John Doe ordered?"
python client/cli.py query "List all customers who ordered furniture items"
```

### Order Details
```bash
python client/cli.py query "Show me all orders with their customer names and product names"
python client/cli.py query "What products are in pending orders?"
python client/cli.py query "Show me the most recent 5 orders with customer and product details"
```

---

## 3. Aggregation & Analytics Queries

### Revenue & Sales Analysis
```bash
python client/cli.py query "What is the total revenue from all completed orders?"
python client/cli.py query "What is the average order value?"
python client/cli.py query "Show me total sales by customer"
python client/cli.py query "Which customer has spent the most money?"
python client/cli.py query "What is the total revenue by product category?"
```

### Product Performance
```bash
python client/cli.py query "Which products have been ordered the most?"
python client/cli.py query "Show me products that have never been ordered"
python client/cli.py query "What is the total quantity sold for each product?"
python client/cli.py query "Which product category generates the most revenue?"
```

### Time-Based Analysis
```bash
python client/cli.py query "How many orders were placed in November 2025?"
python client/cli.py query "Show me orders from the last 30 days"
python client/cli.py query "What was our total revenue last month?"
```

---

## 4. Advanced Queries (Filtering & Conditions)

### Complex Filters
```bash
python client/cli.py query "Show me customers who have ordered products worth more than $100"
python client/cli.py query "List all orders containing laptops or monitors"
python client/cli.py query "Which customers have ordered more than 2 different products?"
python client/cli.py query "Show me pending orders with total value greater than $500"
```

### Comparative Analysis
```bash
python client/cli.py query "Compare total sales between Electronics and Furniture categories"
python client/cli.py query "Show me the price difference between the most and least expensive products"
python client/cli.py query "Which customers have both pending and completed orders?"
```

---

## 5. Chart-Compatible Queries (For Visualization)

### Bar Charts
```bash
# Orders by status
python client/cli.py query "Show me order count by status" --chart

# Products by category
python client/cli.py query "How many products are in each category?" --chart

# Revenue by customer
python client/cli.py query "Show total revenue by customer name" --chart

# Orders by customer
python client/cli.py query "How many orders has each customer placed?" --chart
```

### Revenue Charts
```bash
# Revenue by product category
python client/cli.py query "What is total sales revenue by product category?" --chart

# Revenue by product
python client/cli.py query "Show revenue generated by each product" --chart

# Daily order values
python client/cli.py query "Show total order amount by date" --chart
```

### Product Analysis Charts
```bash
# Most popular products
python client/cli.py query "Show me the quantity sold for each product" --chart

# Price comparison
python client/cli.py query "Compare prices of all products" --chart

# Category distribution
python client/cli.py query "Show distribution of products across categories" --chart
```

---

## 6. Edge Cases & Stress Tests

### Empty Results
```bash
python client/cli.py query "Show me orders from customers named 'Nonexistent Person'"
python client/cli.py query "Which customers ordered a Tesla?"
python client/cli.py query "List orders placed in 2020"
```

### Complex Aggregations
```bash
python client/cli.py query "For each customer, show their total spending, number of orders, and average order value"
python client/cli.py query "Show me products ordered by multiple customers"
python client/cli.py query "Calculate the average price per category and show products above that average"
```

### Sorting & Limits
```bash
python client/cli.py query "Show me the 5 most recent orders with all details"
python client/cli.py query "List top 3 customers by total spending"
python client/cli.py query "Show me the 3 cheapest and 3 most expensive products"
```

---

## 7. Real Business Questions

### Inventory & Stock
```bash
python client/cli.py query "Which products are most popular?"
python client/cli.py query "Show me slow-moving products with less than 2 orders"
python client/cli.py query "What percentage of our products are electronics?"
```

### Customer Insights
```bash
python client/cli.py query "Who are our top 3 customers by order count?"
python client/cli.py query "Which customers only bought once?"
python client/cli.py query "Show me customers with pending orders"
```

### Sales Reports
```bash
python client/cli.py query "Generate a sales summary: total orders, total revenue, average order value"
python client/cli.py query "Show me revenue breakdown by product category with percentages"
python client/cli.py query "What is the completion rate of our orders?"
```

---

## 8. Testing Error Handling

### Invalid Queries
```bash
python client/cli.py query "DROP TABLE customers"  # Should be blocked
python client/cli.py query "DELETE FROM orders"    # Should be blocked
python client/cli.py query "Show me data from nonexistent_table"
```

### Ambiguous Queries
```bash
python client/cli.py query "Show me everything"
python client/cli.py query "What's the deal?"
python client/cli.py query "Give me some data"
```

---

## Quick Test Suite (Run All Core Features)

```bash
# Basic functionality
python client/cli.py query "How many customers do we have?"
python client/cli.py query "Show me all products with their prices"
python client/cli.py query "Are there any pending orders?"

# JOIN queries
python client/cli.py query "Which customers ordered keyboards?"
python client/cli.py query "Show me all orders with customer and product names"

# Aggregations
python client/cli.py query "What is the total revenue from all orders?"
python client/cli.py query "Which customer has spent the most money?"

# Charts
python client/cli.py query "Show order count by status" --chart
python client/cli.py query "Show total revenue by customer" --chart

# Complex
python client/cli.py query "For each product category, show total revenue and number of products"
```

---

## Expected Results Reference

### Key Metrics
- Total customers: **5**
- Total orders: **8**
- Total products: **8**
- Order statuses: **6 completed, 2 pending**
- Product categories: **Electronics (4), Furniture (2), Stationery (2)**

### Notable Data Points
- John Doe ordered: Laptop, Mouse, Keyboard
- Customer with most expensive pending order: Bob Johnson ($1,299.99 - Laptop)
- Cheapest product: Notebook ($5.99)
- Most expensive product: Laptop ($1,299.99)
