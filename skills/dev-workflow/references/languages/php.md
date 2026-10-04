# PHP (Laravel)
| Topic | Convention |
| --- | --- |
| Tooling | **Composer**; **Laravel Pint** (PSR-12 plus the Laravel preset); **Larastan** at the highest level the project can sustain; Pest for tests. |
| Laravel naming | Models singular `PascalCase` (`Order`); tables plural `snake_case` (`order_items`); controllers singular plus `Controller` (`OrderController`); Form Requests `StoreOrderRequest`/`UpdateOrderRequest`; Actions as verb + noun (`CreateOrder`); Resources `OrderResource`; route URIs plural kebab-case (`/order-items`); route names dotted (`orders.show`). |
| Code | `declare(strict_types=1);` in domain and application classes; typed properties, parameters and return types everywhere; constructor property promotion; backed enums instead of string constants. |
