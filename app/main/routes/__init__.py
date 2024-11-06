from app.main import bp
from app.main.routes import general, admin, manager, valet, customer, utility, websocket, auth
# Import all route modules
from app.main.routes import general, admin, manager, valet, customer, utility, websocket

# login and logout routes
bp.add_url_rule('/login', 'login', auth.login, methods=['GET', 'POST'])
bp.add_url_rule('/logout', 'logout', auth.logout)

# Register general routes
bp.add_url_rule('/', 'index', general.index)
bp.add_url_rule('/index', 'index', general.index)
bp.add_url_rule('/profile', 'user_profile', general.user_profile, methods=['GET', 'POST'])

# Register admin routes
bp.add_url_rule('/admin_dashboard', 'admin_dashboard', admin.admin_dashboard)
bp.add_url_rule('/admin/users', 'admin_users', admin.admin_users)
bp.add_url_rule('/admin/sessions', 'admin_sessions', admin.admin_sessions)
bp.add_url_rule('/admin/report', 'admin_report', admin.admin_report)
bp.add_url_rule('/admin/api/session_data', 'admin_session_data', admin.admin_session_data)
bp.add_url_rule('/admin/create_user', 'admin_create_user', admin.admin_create_user, methods=['GET', 'POST'])
bp.add_url_rule('/admin/edit_user/<int:user_id>', 'admin_edit_user', admin.admin_edit_user, methods=['GET', 'POST'])

# Register manager routes
bp.add_url_rule('/manager_dashboard', 'manager_dashboard', manager.manager_dashboard)
bp.add_url_rule('/manager/valet_attendants', 'manage_valet_attendants', manager.manage_valet_attendants)
bp.add_url_rule('/manager/valet_attendant/add', 'add_valet_attendant', manager.add_valet_attendant, methods=['GET', 'POST'])
bp.add_url_rule('/manager/valet_attendant/edit/<int:id>', 'edit_valet_attendant', manager.edit_valet_attendant, methods=['GET', 'POST'])
bp.add_url_rule('/manager/valet_attendant/delete/<int:id>', 'delete_valet_attendant', manager.delete_valet_attendant, methods=['POST'])
bp.add_url_rule('/manager/stations', 'manage_stations', manager.manage_stations)
bp.add_url_rule('/manager/station/add', 'add_station', manager.add_station, methods=['GET', 'POST'])
bp.add_url_rule('/manager/station/edit/<int:id>', 'edit_station', manager.edit_station, methods=['GET', 'POST'])
bp.add_url_rule('/manager/station/delete/<int:id>', 'delete_station', manager.delete_station, methods=['POST'])
bp.add_url_rule('/manager/assign_valet/<int:valet_id>/to_station/<int:station_id>', 'assign_valet_to_station', manager.assign_valet_to_station, methods=['POST'])
bp.add_url_rule('/manager_dashboard', 'manager_dashboard', manager.manager_dashboard)
bp.add_url_rule('/manager/valet_attendants', 'manage_valet_attendants', manager.manage_valet_attendants)
bp.add_url_rule('/manager/valet_attendant/assign', 'assign_valet_to_station', manager.assign_valet_to_station, methods=['POST'])
bp.add_url_rule('/manager/valet_attendant/edit_attendant/<int:valet_id>', 'edit_valet_attendant', manager.edit_valet_attendant, methods=['GET', 'POST'])
bp.add_url_rule('/manager/valet_attendant/edit/<int:id>', 'edit_valet_attendant', manager.edit_valet_attendant, methods=['GET', 'POST'])
bp.add_url_rule('/manager/station/<int:station_id>/spaces', 'manage_spaces', manager.manage_spaces, methods=['GET', 'POST'])
bp.add_url_rule('/manager/station/<int:station_id>/spaces/<space>/delete', 'delete_space', manager.delete_space, methods=['POST'])
bp.add_url_rule('/manager/station/<int:station_id>/spaces/edit/<string:old_space>', 'edit_space', manager.edit_space, methods=['POST'])
bp.add_url_rule('/manager/station/<int:station_id>/spaces/add', 'add_space', manager.add_space, methods=['POST'])

# Register valet routes
bp.add_url_rule('/valet_dashboard', 'valet_dashboard', valet.valet_dashboard)
bp.add_url_rule('/valet/park_car', 'valet_park_car', valet.valet_park_car, methods=['GET', 'POST'])
bp.add_url_rule('/valet/car_ready/<int:session_id>', 'valet_car_ready', valet.valet_car_ready, methods=['POST'])
bp.add_url_rule('/valet/pick_up_car/<int:session_id>', 'valet_pick_up_car', valet.valet_pick_up_car, methods=['POST'])
# Register customer routes
bp.add_url_rule('/customer_portal/<int:session_id>', 'customer_portal', customer.customer_portal)
bp.add_url_rule('/customer_request_car/<int:session_id>', 'customer_request_car', customer.customer_request_car, methods=['POST'])
bp.add_url_rule('/customer_portal/test-websocket', 'test_websocket', customer.test_websocket)
# Register utility routes
bp.add_url_rule('/generate_qr/<int:session_id>', 'generate_qr', utility.generate_qr)

# general api routes
bp.add_url_rule('/api/session/<int:session_id>/time_parked', 'get_time_parked', valet.get_time_parked)

# landing route
bp.add_url_rule('/landing', 'landing', general.landing)



