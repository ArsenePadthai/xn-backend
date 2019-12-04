import xlrd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from XNBackend.models import IRSensors, TcpConfig

def xx():
    ENGINE = create_engine('mysql+pymysql://xn:Pass1234@10.100.101.199:3306/xn?charset=utf8mb4', echo=True)
    Session = sessionmaker(bind=ENGINE)
    session = Session()


    xl = xlrd.open_workbook("D:\\test.xlsx")
    m=xl.sheet_by_index(0)

    for i in range(m.nrows):
        room = str(int(m.cell_value(i, 0)))
        addr = int(m.cell_value(i, 1))
        ip = '10.100.102.'+str(int(m.cell_value(i, 2)))
        tcp_config = session.query(TcpConfig).filter(TcpConfig.ip==ip).first()
        ir = IRSensors(batch_no=0, addr_no=addr, locator=room, tcp_config_id=tcp_config.id)
        session.add(ir)
    session.commit()


if __name__ == "__main__":
    xx()