from app.main import bp
from app.main.routes import general, admin, manager, valet, customer, utility

# Register routes from general
bp.add_url_rule('/', 'index', general.index)
bp.add_url_rule('/index', 'index', general.index)
bp.add_url_rule('/profile', 'user_profile', general.user_profile, methods=['GET', 'POST'])

# Register routes from admin
bp.add_url_rule('/admin_dashboard', 'admin_dashboard', admin.admin_dashboard)
bp.add_url_rule('/admin/users', 'admin_users', admin.admin_users)
bp.add_url_rule('/admin/sessions', 'admin_sessions', admin.admin_sessions)
bp.add_url_rule('/admin/report', 'admin_report', admin.admin_report)
bp.add_url_rule('/admin/api/session_data', 'admin_session_data', admin.admin_session_data)
bp.add_url_rule('/admin/create_user', 'admin_create_user', admin.admin_create_user, methods=['GET', 'POST'])
bp.add_url_rule('/admin/edit_user/<int:user_id>', 'admin_edit_user', admin.admin_edit_user, methods=['GET', 'POST'])

# Register routes from manager
bp.add_url_rule('/manager_dashboard', 'manager_dashboard', manager.manager_dashboard)
bp.add_url_rule('/manager/valet_attendants', 'manager_valet_attendants', manager.manager_valet_attendants)
bp.add_url_rule('/manager/valet_attendant/new', 'new_valet_attendant', manager.new_valet_attendant, methods=['GET', 'POST'])
bp.add_url_rule('/manager/valet_attendant/edit/<int:id>', 'edit_valet_attendant', manager.edit_valet_attendant, methods=['GET', 'POST'])
bp.add_url_rule('/manager/valet_attendant/delete/<int:id>', 'delete_valet_attendant', manager.delete_valet_attendant, methods=['POST'])
bp.add_url_rule('/manager/valet_posts', 'manager_valet_posts', manager.manager_valet_posts)
bp.add_url_rule('/manager/valet_post/new', 'new_valet_post', manager.new_valet_post, methods=['GET', 'POST'])
bp.add_url_rule('/manager/valet_post/edit/<int:id>', 'edit_valet_post', manager.edit_valet_post, methods=['GET', 'POST'])
bp.add_url_rule('/manager/valet_post/delete/<int:id>', 'delete_valet_post', manager.delete_valet_post, methods=['POST'])

# Register routes from valet
bp.add_url_rule('/valet_dashboard', 'valet_dashboard', valet.valet_dashboard)
bp.add_url_rule('/valet/park_car', 'valet_park_car', valet.valet_park_car, methods=['GET', 'POST'])
bp.add_url_rule('/valet/retrieve_car/<int:session_id>', 'valet_retrieve_car', valet.valet_retrieve_car, methods=['GET', 'POST'])
bp.add_url_rule('/valet/session/<int:session_id>', 'valet_session_details', valet.valet_session_details)
bp.add_url_rule('/valet/request_car/<int:session_id>', 'valet_request_car', valet.valet_request_car, methods=['POST'])

# Register routes from customer
bp.add_url_rule('/customer_portal/<int:session_id>', 'customer_portal', customer.customer_portal)
bp.add_url_rule('/customer_request_car/<int:session_id>', 'customer_request_car', customer.customer_request_car, methods=['POST'])

# Register routes from utility
bp.add_url_rule('/generate_qr/<int:session_id>', 'generate_qr', utility.generate_qr)

