import streamlit as st
import pandas as pd
import pyodbc
import time
import hashlib


# ==================== 数据库配置部分 ====================
def create_connection():
    server = 'localhost'  # 数据库服务器地址
    database = '仓库管理系统'  # 数据库名称
    username = 'your_username'  # 数据库用户名
    password = 'your_password'  # 数据库密码
    driver = '{ODBC Driver 17 for SQL Server}'  # ODBC 驱动

    try:
        conn = pyodbc.connect(
            f'DRIVER={driver};'
            f'SERVER={server};'
            f'DATABASE={database};'
            f'UID={username};'
            f'PWD={password}'
        )
        print("数据库连接成功")
        return conn
    except Exception as e:
        print(f"数据库连接失败: {str(e)}")
        return None


# ==================== 数据库操作类 ====================
class WarehouseDB:
    def __init__(self):
        self.conn = create_connection()

    def execute_query(self, query, params=None):
        """执行查询并返回结果"""
        if not self.conn:
            return None

        try:
            cursor = self.conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # 如果是SELECT查询
            if query.strip().upper().startswith('SELECT'):
                columns = [column[0] for column in cursor.description]
                results = cursor.fetchall()
                if results:
                    return pd.DataFrame.from_records(results, columns=columns)
                else:
                    return pd.DataFrame()
            else:
                self.conn.commit()
                return cursor.rowcount
        except Exception as e:
            print(f"查询执行失败: {str(e)}")
            return None
        finally:
            if 'cursor' in locals():
                cursor.close()

    def get_products(self):
        """获取所有商品信息"""
        return self.execute_query("SELECT * FROM 商品信息")

    def get_inventory(self):
        """获取当前库存"""
        return self.execute_query("SELECT * FROM 当前库存")

    def add_product(self, name, spec, unit, category_id, safety_stock):
        """添加新商品"""
        query = """
        INSERT INTO 商品信息 (商品名称, 规格型号, 单位, 分类编号, 安全库存)
        VALUES (?, ?, ?, ?, ?)
        """
        return self.execute_query(query, (name, spec, unit, category_id, safety_stock))

    def stock_in(self, product_id, quantity, operator_id, supplier):

        """商品入库"""
        query = """
                EXEC 商品入库 @商品编号=?, @数量=?, @操作员编号=?, @供应商=?
                """
        return self.execute_query(query, (product_id, quantity, operator_id, supplier))

    def stock_out(self, product_id, quantity, operator_id, customer):
        """商品出库"""
        query = """
                INSERT INTO 出库记录 (商品编号, 数量, 操作员编号, 客户名称)
                VALUES (?, ?, ?, ?)
                """
        return self.execute_query(query, (product_id, quantity, operator_id, customer))

    def get_users(self):
        """获取所有用户"""
        return self.execute_query("SELECT * FROM 用户账户")

    def get_stock_in_records(self):
        """获取入库记录"""
        return self.execute_query("SELECT * FROM 入库记录")

    def get_stock_out_records(self):
        """获取出库记录"""
        return self.execute_query("SELECT * FROM 出库记录")

    def get_logs(self):
        """获取系统日志"""
        return self.execute_query("SELECT * FROM 系统日志 ORDER BY 操作时间 DESC")

    def add_user(self, username, password, role):
        """添加新用户"""
        query = """
                INSERT INTO 用户账户 (用户名, 密码, 角色)
                VALUES (?, ?, ?)
                """
        return self.execute_query(query, (username, password, role))

    def update_product(self, product_id, name, spec, unit, category_id, safety_stock):
        """更新商品信息"""
        query = """
                UPDATE 商品信息 
                SET 商品名称=?, 规格型号=?, 单位=?, 分类编号=?, 安全库存=?
                WHERE 商品编号=?
                """
        return self.execute_query(query, (name, spec, unit, category_id, safety_stock, product_id))

    def log_action(self, action_type, details, user_id):
        """记录系统日志"""
        query = """
                INSERT INTO 系统日志 (操作类型, 详细信息, 用户编号)
                VALUES (?, ?, ?)
                """
        return self.execute_query(query, (action_type, details, user_id))

    def close_connection(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            print("数据库连接已关闭")
            self.conn = None

    # ==================== 主程序部分 ====================


def main():
    # 初始化数据库连接
    db = WarehouseDB()

    # 页面设置
    st.set_page_config(
        page_title="仓库管理系统",
        layout="wide",
        page_icon="📦",
        initial_sidebar_state="expanded"
    )

    # 自定义CSS样式
    st.markdown("""
            <style>
                .main {background-color: #f5f5f5;}
                .st-bb {background-color: white;}
                .st-at {background-color: #e6f7ff;}
                .stButton>button {
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 5px;
                    padding: 0.5rem 1rem;
                    font-weight: bold;
                }
                .stAlert {border-radius: 10px;}
                .sidebar .sidebar-content {
                    background-color: #f0f2f6;
                }
                .header-title {
                    font-size: 2.5rem;
                    font-weight: bold;
                    color: #1e3c72;
                    text-align: center;
                    padding: 1rem;
                    margin-bottom: 2rem;
                    background: linear-gradient(to right, #1e3c72, #2a5298);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }
                .section-title {
                    border-bottom: 2px solid #1e3c72;
                    padding-bottom: 0.5rem;
                    margin-bottom: 1.5rem;
                    color: #1e3c72;
                }
                .low-stock {
                    background-color: #fff2cc !important;
                }
                .critical-stock {
                    background-color: #f8cecc !important;
                }
                .dataframe {
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }
            </style>
            """, unsafe_allow_html=True)
    # 页面标题
    st.markdown('<h1 class="header-title">📦 仓库管理系统</h1>', unsafe_allow_html=True)

    # 登录功能
    def login():
        st.sidebar.title("用户登录")
        username = st.sidebar.text_input("用户名")
        password = st.sidebar.text_input("密码", type="password")

        if st.sidebar.button("登录"):
            if not username or not password:
                st.sidebar.warning("请输入用户名和密码")
                return

            users = db.get_users()
            if users.empty:
                st.sidebar.error("数据库中没有用户数据")
                return

            user = users[(users['用户名'] == username) & (users['密码'] == password)]

            if not user.empty:
                st.session_state['logged_in'] = True
                st.session_state['user_id'] = user['用户编号'].values[0]
                st.session_state['username'] = user['用户名'].values[0]
                st.session_state['role'] = user['角色'].values[0]
                st.sidebar.success(f"欢迎回来, {st.session_state['username']} ({st.session_state['role']})")
                # 记录登录日志
                db.log_action('登录', f"用户 {username} 登录系统", st.session_state['user_id'])
            else:
                st.sidebar.error("用户名或密码错误")

    # 如果没有登录，显示登录界面
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        login()
        st.info("请使用侧边栏登录系统")
        st.image(
            "https://images.unsplash.com/photo-1603739903239-8b6e64c3b185?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80",
            caption="仓库管理系统", use_column_width=True)
        db.close_connection()
        return

    # 主菜单
    menu_options = {
        "商品管理": ["商品信息", "新增商品"],
        "入库管理": ["入库记录", "新增入库"],
        "出库管理": ["出库记录", "新增出库"],
        "库存管理": ["当前库存"],
        "系统管理": ["用户管理", "系统日志"]
    }

    # 根据用户角色显示可用菜单
    if st.session_state['role'] == '操作员':
        menu_options = {
            "入库管理": ["新增入库"],
            "出库管理": ["新增出库"],
            "库存管理": ["当前库存"]
        }
    elif st.session_state['role'] == '经理':
        menu_options = {
            "商品管理": ["商品信息"],
            "入库管理": ["入库记录", "新增入库"],
            "出库管理": ["出库记录", "新增出库"],
            "库存管理": ["当前库存"]
        }

    # 显示侧边栏菜单
    st.sidebar.title("功能菜单")
    selected_category = st.sidebar.radio("选择功能", list(menu_options.keys()))
    selected_option = st.sidebar.selectbox("选择操作", menu_options[selected_category])

    # 显示当前用户信息
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**当前用户**: {st.session_state['username']}")
    st.sidebar.markdown(f"**用户角色**: {st.session_state['role']}")

    # 退出按钮
    if st.sidebar.button("退出系统"):
        # 记录退出日志
        db.log_action('退出', f"用户 {st.session_state['username']} 退出系统", st.session_state['user_id'])

        st.session_state.clear()
        st.sidebar.success("已成功退出系统")
        time.sleep(1)
        st.experimental_rerun()

    # 商品管理
    if selected_category == "商品管理":
        if selected_option == "商品信息":
            st.subheader("商品信息管理")
            products = db.get_products()

            if not products.empty:
                # 添加库存信息
                inventory = db.get_inventory()
                if not inventory.empty:
                    products = products.merge(inventory[['商品编号', '当前库存量']], on='商品编号', how='left')

                # 标记低库存商品
                def highlight_low_stock(row):
                    if row['安全库存'] > 0 and row['当前库存量'] < row['安全库存']:
                        return ['background-color: #fff2cc'] * len(row)
                    return [''] * len(row)

                st.dataframe(products.style.apply(highlight_low_stock, axis=1))

                # 编辑功能（仅管理员）
                if st.session_state['role'] == '管理员':
                    st.markdown("---")
                    st.subheader("编辑商品信息")

                    selected_product = st.selectbox("选择商品编辑", products['商品名称'])
                    product_details = products[products['商品名称'] == selected_product].iloc[0]

                    with st.form("编辑商品表单"):
                        st.write(f"编辑商品: **{selected_product}**")
                        new_name = st.text_input("商品名称", value=product_details['商品名称'])
                        new_spec = st.text_input("规格型号", value=product_details['规格型号'])
                        new_unit = st.text_input("单位", value=product_details['单位'])
                        new_category = st.number_input("分类编号", min_value=1, value=product_details['分类编号'])
                        new_safety = st.number_input("安全库存", min_value=0, value=product_details['安全库存'])

                        if st.form_submit_button("更新商品"):
                            if new_name:
                                result = db.update_product(
                                    product_details['商品编号'],
                                    new_name, new_spec, new_unit,
                                    new_category, new_safety
                                )

                                if result == 1:
                                    st.success("商品信息更新成功！")
                                    # 记录日志
                                    db.log_action('商品修改', f"修改商品: {selected_product}",
                                                  st.session_state['user_id'])
                                    time.sleep(1)
                                    st.experimental_rerun()
                                else:
                                    st.error("更新失败")
                            else:
                                st.warning("商品名称不能为空")
                else:
                    st.info("没有商品数据")

            elif selected_option == "新增商品":
                st.subheader("新增商品")
                with st.form("新增商品表单"):
                    name = st.text_input("商品名称", max_chars=100)
                    spec = st.text_input("规格型号", max_chars=50)
                    unit = st.text_input("单位", max_chars=20)
                    category = st.number_input("分类编号", min_value=1)
                    safety_stock = st.number_input("安全库存", min_value=0)

                    if st.form_submit_button("添加商品"):
                        if name and unit:
                            result = db.add_product(name, spec, unit, category, safety_stock)
                            if result == 1:
                                st.success("商品添加成功！")
                                # 记录日志
                                db.log_action('商品添加', f"添加商品: {name}", st.session_state['user_id'])
                                time.sleep(1)
                                st.experimental_rerun()
                            else:
                                st.error("添加失败")
                        else:
                            st.warning("请填写必填字段（商品名称和单位）")

            # 入库管理
            elif selected_category == "入库管理":
                if selected_option == "入库记录":
                    st.subheader("入库记录查询")
                    records = db.get_stock_in_records()

                    if not records.empty:
                        # 添加商品名称
                        products = db.get_products()
                        if not products.empty:
                            records = records.merge(products[['商品编号', '商品名称']], on='商品编号', how='left')

                        # 添加操作员名称
                        users = db.get_users()
                        if not users.empty:
                            records = records.merge(users[['用户编号', '用户名']],
                                                    left_on='操作员编号', right_on='用户编号',
                                                    how='left')
                            records = records.rename(columns={'用户名': '操作员'})

                        # 显示入库记录
                        st.dataframe(records[['入库单号', '商品名称', '数量', '入库时间', '供应商', '操作员']])
                    else:
                        st.info("没有入库记录")

                elif selected_option == "新增入库":
                    st.subheader("新增入库记录")
                    products = db.get_products()

                    if not products.empty:
                        product_names = products['商品名称'].tolist()

                        with st.form("入库表单"):
                            product_name = st.selectbox("选择商品", product_names)
                            product_id = products[products['商品名称'] == product_name]['商品编号'].values[0]
                            quantity = st.number_input("入库数量", min_value=1, value=1)
                            supplier = st.text_input("供应商")

                            if st.form_submit_button("提交入库"):
                                result = db.stock_in(
                                    product_id,
                                    quantity,
                                    st.session_state['user_id'],
                                    supplier
                                )
                                if result == 1:
                                    st.success("入库记录添加成功！")
                                    time.sleep(1)
                                    st.experimental_rerun()
                                else:
                                    st.error("入库失败")
                    else:
                        st.warning("请先添加商品")

                    # 出库管理
                elif selected_category == "出库管理":
                    if selected_option == "出库记录":
                        st.subheader("出库记录查询")
                        records = db.get_stock_out_records()

                        if not records.empty:
                            # 添加商品名称
                            products = db.get_products()
                            if not products.empty:
                                records = records.merge(products[['商品编号', '商品名称']], on='商品编号', how='left')

                            # 添加操作员名称
                            users = db.get_users()
                            if not users.empty:
                                records = records.merge(users[['用户编号', '用户名']],
                                                        left_on='操作员编号', right_on='用户编号',
                                                        how='left')
                                records = records.rename(columns={'用户名': '操作员'})

                            # 显示出库记录
                            st.dataframe(records[['出库单号', '商品名称', '数量', '出库时间', '客户名称', '操作员']])
                        else:
                            st.info("没有出库记录")

                    elif selected_option == "新增出库":
                        st.subheader("新增出库记录")
                        inventory = db.get_inventory()

                        if not inventory.empty:
                            # 过滤掉库存为0的商品
                            available_products = inventory[inventory['当前库存量'] > 0]

                            if available_products.empty:
                                st.warning("没有可出库的商品")
                            else:
                                product_names = available_products['商品名称'].tolist()

                                with st.form("出库表单"):
                                    product_name = st.selectbox("选择商品", product_names)
                                    product_id = available_products[
                                        available_products['商品名称'] == product_name
                                        ]['商品编号'].values[0]

                                    max_quantity = available_products[
                                        available_products['商品名称'] == product_name
                                        ]['当前库存量'].values[0]

                                    quantity = st.number_input("出库数量", min_value=1, max_value=max_quantity, value=1)
                                    customer = st.text_input("客户名称")

                                    if st.form_submit_button("提交出库"):
                                        result = db.stock_out(
                                            product_id,
                                            quantity,
                                            st.session_state['user_id'],
                                            customer
                                        )
                                        if result == 1:
                                            st.success("出库记录添加成功！")
                                            # 记录日志
                                            db.log_action('出库', f"出库: {quantity}个 {product_name} 给 {customer}",
                                                          st.session_state['user_id'])
                                            time.sleep(1)
                                            st.experimental_rerun()
                                        else:
                                            st.error("出库失败")
                        else:
                            st.warning("没有库存数据")

                # 库存管理
                elif selected_category == "库存管理":
                    st.subheader("当前库存情况")
                    inventory = db.get_inventory()

                    if not inventory.empty:
                        # 添加库存状态
                        def get_stock_status(row):
                            if row['安全库存'] == 0:
                                return "正常"
                            elif row['当前库存量'] > row['安全库存']:
                                return "充足"
                            elif row['当前库存量'] > row['安全库存'] * 0.5:
                                return "预警"
                            else:
                                return "严重不足"

                        inventory['库存状态'] = inventory.apply(get_stock_status, axis=1)

                        # 库存预警
                        low_stock = inventory[inventory['库存状态'] != "充足"]
                        if not low_stock.empty:
                            st.warning("以下商品库存需要关注:")
                            st.dataframe(low_stock[['商品名称', '当前库存量', '安全库存', '库存状态']])

                        # 显示所有库存
                        st.dataframe(inventory[['商品名称', '单位', '当前库存量', '安全库存', '库存状态']])

                        # 库存分析图表
                        st.subheader("库存分析")

                        # 库存状态分布
                        status_counts = inventory['库存状态'].value_counts().reset_index()
                        status_counts.columns = ['库存状态', '商品数量']
                        st.bar_chart(status_counts.set_index('库存状态'))

                        # 库存量TOP10
                        st.subheader("库存量TOP10")
                        top10 = inventory.nlargest(10, '当前库存量')
                        st.bar_chart(top10.set_index('商品名称')['当前库存量'])

                        # 库存量BOTTOM10
                        st.subheader("库存量BOTTOM10")
                        bottom10 = inventory.nsmallest(10, '当前库存量')
                        st.bar_chart(bottom10.set_index('商品名称')['当前库存量'])
                    else:
                        st.info("没有库存数据")

                        # 系统管理
                elif selected_category == "系统管理" and st.session_state['role'] == '管理员':
                    if selected_option == "用户管理":
                        st.subheader("用户管理")
                        users = db.get_users()

                        if not users.empty:
                            st.dataframe(users[['用户名', '角色']])

                            # 添加用户
                            st.subheader("添加新用户")
                            with st.form("添加用户表单"):
                                username = st.text_input("用户名")
                                password = st.text_input("密码", type="password")
                                confirm_password = st.text_input("确认密码", type="password")
                                role = st.selectbox("角色", ['管理员', '经理', '操作员'])

                                if st.form_submit_button("添加用户"):
                                    if username and password:
                                        if password != confirm_password:
                                            st.error("两次输入的密码不一致")
                                        else:
                                            result = db.add_user(username, password, role)
                                            if result == 1:
                                                st.success("用户添加成功！")
                                                # 记录日志
                                                db.log_action('用户添加', f"添加用户: {username}",
                                                              st.session_state['user_id'])
                                                time.sleep(1)
                                                st.experimental_rerun()
                                            else:
                                                st.error("添加失败")
                                    else:
                                        st.warning("请填写用户名和密码")
                        else:
                            st.info("没有用户数据")

                    elif selected_option == "系统日志":
                        st.subheader("系统操作日志")
                        logs = db.get_logs()

                        if not logs.empty:
                            # 添加用户名
                            users = db.get_users()
                            if not users.empty:
                                logs = logs.merge(users[['用户编号', '用户名']], on='用户编号', how='left')

                            st.dataframe(logs[['操作时间', '操作类型', '详细信息', '用户名']])
                        else:
                            st.info("没有日志记录")

                    # 关闭数据库连接
                db.close_connection()

                if __name__ == "__main__":
                    main()