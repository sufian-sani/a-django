// =============================
// POS Application Database Schema
// =============================

Table orders {
  id             int          [pk, increment]
  status         varchar(20)  [default: 'Pending', note: 'Pending | Completed | Cancelled']
  customer_id    int          [ref: > customers.id, null] // Nullable for walk-ins
  created_at     timestamp    [default: `now()`]
  updated_at     timestamp    [default: `now()`]
}

Table products {
  id                int      [pk, increment]
  name              varchar(255)
  description       text
  price             decimal(10,2)
}

Table order_items {
  id                int      [pk, increment]
  order_id          int      [ref: > orders.id]       // FK to Order
  product_id        int      [ref: > products.id]     // FK to Product
  quantity          int      [default: 1]
  price_at_time_of_order decimal(10,2)
}

Table invoices {
  id                int      [pk, increment]
  order_id          int      [ref: > orders.id, not null]
  invoice_number    varchar(50) [unique]
  split_type        varchar(20) [default: 'full', note: 'full | item_wise | amount_wise']
  status            varchar(20) [default: 'Unpaid', note: 'Paid | Unpaid | Overdue | Cancelled']
  is_split          boolean  [default: false]
  subtotal_amount   decimal(10,2) [default: 0]
  tax_amount        decimal(10,2) [default: 0]
  discount_amount   decimal(10,2) [default: 0]
  total_amount      decimal(10,2) [default: 0]
  paid_amount       decimal(10,2) [default: 0]
  balance_amount    decimal(10,2) [default: 0]
  issued_at         timestamp [default: `now()`]
}

Table customers {
  id         int       [pk, increment]
  name       varchar(255)  [not null]
  email      varchar(255)  [unique]
  phone      varchar(50)
  address    text
  created_at timestamp [default: `now()`]
  updated_at timestamp [default: `now()`]
}

Table payments {
  id            int      [pk, increment]
  invoice_id    int      [ref: > invoices.id, not null]
  customer_id   int      [ref: > customers.id]   // Nullable for walk‑ins
  amount        decimal(10,2) [not null]
  payment_method        varchar(20)
  reference     varchar(100)  // Gateway txn ID, card auth code, etc.
  paid_at       timestamp [default: `now()`]
}

Table invoice_items {
  id                int      [pk, increment]
  invoice_id        int      [ref: > invoices.id, not null]
  order_item_id     int      [ref: > order_items.id, not null]
  quantity          int      [default: 1]
  unit_price        decimal(10,2)
  subtotal          decimal(10,2)
  tax_amount        decimal(10,2) [default: 0]
  discount_amount   decimal(10,2) [default: 0]
  total_amount      decimal(10,2)
  paid_amount       decimal(10,2) [default: 0]
  balance_amount    decimal(10,2) [default: 0]

  Indexes {
    (invoice_id, order_item_id) [unique]
  }
}

Table payment_allocations {
  id               int      [pk, increment]
  payment_id       int      [ref: > payments.id, not null]
  invoice_item_id  int      [ref: > invoice_items.id, not null]
  allocated_amount decimal(10,2) [not null]
  allocated_at     timestamp [default: `now()`]

  Indexes {
    (payment_id, invoice_item_id) [unique]
  }
}