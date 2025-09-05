import io
from datetime import datetime
from typing import List, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

def register_chinese_fonts():
    """注册中文字体，带多种fallback选项和更强的错误处理"""
    try:
        # 尝试多个字体路径
        font_paths = [
            "C:/Windows/Fonts/msyh.ttc",        # 微软雅黑
            "C:/Windows/Fonts/msyh.ttf",        # 微软雅黑 TTF
            "C:/Windows/Fonts/simhei.ttf",      # 黑体
            "C:/Windows/Fonts/simsun.ttc",      # 宋体
            "C:/Windows/Fonts/simsun.ttf",      # 宋体 TTF
            "/System/Library/Fonts/PingFang.ttc",  # macOS
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
        ]
        
        font_registered = False
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    print(f"尝试注册字体: {font_path}")
                    pdfmetrics.registerFont(TTFont('SimHei', font_path))
                    print(f"成功注册字体: {font_path}")
                    font_registered = True
                    break
                else:
                    print(f"字体文件不存在: {font_path}")
            except Exception as e:
                print(f"字体注册失败 {font_path}: {e}")
                continue
        
        if not font_registered:
            # 如果所有系统字体都失败，尝试创建一个简单的测试字体
            try:
                # 使用内置字体作为最终备用方案
                print("所有系统字体都无法使用，使用内置字体作为备用")
                return False
            except Exception as e:
                print(f"备用字体设置失败: {e}")
                return False
            
    except Exception as e:
        print(f"字体注册过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return font_registered

def create_room_communication_pdf(
    room_info: dict,
    customer_info: Optional[dict],
    communications: List[dict],
    quality_issues: List[dict],
    assigned_users: dict,
    latest_customer_description: str = ""
) -> bytes:
    """生成房间沟通记录PDF"""
    
    # 尝试注册中文字体
    font_registered = register_chinese_fonts()
    
    # 根据字体注册情况选择字体
    if font_registered:
        font_name = 'SimHei'
        print("使用中文字体生成PDF")
    else:
        font_name = 'Helvetica'
        print("使用Helvetica字体生成PDF")
    
    # 创建PDF文档
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2*cm,
        bottomMargin=2*cm,
        leftMargin=2*cm,
        rightMargin=2*cm
    )
    
    # 样式设置
    styles = getSampleStyleSheet()
    
    # 标题样式
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    # 正文样式
    content_style = ParagraphStyle(
        'CustomContent',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        alignment=TA_LEFT
    )
    
    # 构建PDF内容
    story = []
    
    # 标题
    title = f"瑧湾悦二期{room_info.get('building_unit', '')}{room_info.get('room_number', '')} 业主沟通一户一档记录表"
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 20))
    
    # 基本信息表格
    basic_info_data = [
        ['客户姓名', customer_info.get('name', '') if customer_info else '', '性别', customer_info.get('gender', '') if customer_info else ''],
        ['身份证号', customer_info.get('id_card', '') if customer_info else '', '手机号', customer_info.get('phone', '') if customer_info else ''],
        ['客户分级', customer_info.get('customer_level', '') if customer_info else '', '工作单位', customer_info.get('work_unit', '') if customer_info else ''],
        ['维修工程师责任人', assigned_users.get('maintenance_engineer', ''), '客户大使责任人', assigned_users.get('customer_ambassador', '')],
        ['客户高像描摹', latest_customer_description, '', '']
    ]
    
    basic_info_table = Table(basic_info_data, colWidths=[4*cm, 6*cm, 2.5*cm, 4*cm])
    basic_info_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('SPAN', (1, 4), (3, 4)),  # 客户描摹跨列
    ]))
    
    story.append(basic_info_table)
    story.append(Spacer(1, 20))
    
    # 客户沟通过程记录
    story.append(Paragraph("客户沟通过程记录表", content_style))
    story.append(Spacer(1, 10))
    
    comm_header = ['参考范例如下', '', '', '']
    comm_data = [comm_header]
    
    # 按时间排序沟通记录
    sorted_comms = sorted(communications, key=lambda x: x.get('communication_time', x.get('created_at', '')))
    
    comm_content = []
    for comm in sorted_comms:
        comm_time = comm.get('communication_time', comm.get('created_at', ''))
        if isinstance(comm_time, str):
            try:
                time_obj = datetime.fromisoformat(comm_time.replace('Z', '+00:00'))
                time_str = time_obj.strftime('%m月%d日')
            except:
                time_str = comm_time[:10] if len(comm_time) >= 10 else comm_time
        else:
            time_str = ''
            
        content = comm.get('content', '')
        comm_content.append(f"{time_str}：{content}")
    
    comm_text = '；'.join(comm_content)
    if len(comm_text) > 500:  # 限制长度
        comm_text = comm_text[:500] + "..."
    
    comm_data.append([comm_text, '', '', ''])
    
    comm_table = Table(comm_data, colWidths=[16.5*cm])
    comm_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('SPAN', (0, 0), (3, 0)),  # 标题跨列
        ('SPAN', (0, 1), (3, 1)),  # 内容跨列
    ]))
    
    story.append(comm_table)
    story.append(Spacer(1, 20))
    
    # 客户核心诉求
    story.append(Paragraph("客户核心诉求", content_style))
    story.append(Spacer(1, 10))
    
    feedback_content = []
    for comm in communications:
        if comm.get('feedback'):
            feedback_content.append(comm['feedback'])
    
    feedback_text = '；'.join(feedback_content) if feedback_content else '无'
    feedback_data = [['客户核心诉求', feedback_text, '', '']]
    
    feedback_table = Table(feedback_data, colWidths=[3*cm, 13.5*cm])
    feedback_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('SPAN', (1, 0), (3, 0)),  # 内容跨列
    ]))
    
    story.append(feedback_table)
    story.append(Spacer(1, 20))
    
    # 维修问题指导
    story.append(Paragraph("维修问题指导", content_style))
    story.append(Spacer(1, 10))
    
    # 过滤未验收的质量问题
    pending_issues = [issue for issue in quality_issues if issue.get('status') != '已验收']
    
    issue_header = [['维修问题指导', '关闭时间', '跟进维修责任人']]
    issue_data = issue_header
    
    if pending_issues:
        for issue in pending_issues:
            created_time = issue.get('created_at', '')
            if isinstance(created_time, str):
                try:
                    time_obj = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                    time_str = time_obj.strftime('%Y-%m-%d')
                except:
                    time_str = created_time[:10] if len(created_time) >= 10 else created_time
            else:
                time_str = ''
                
            issue_data.append([
                issue.get('description', ''),
                time_str,
                issue.get('user_name', '')
            ])
    else:
        issue_data.append(['无未验收问题', '', ''])
    
    # 添加空行
    for i in range(3 - len(issue_data) + 1):
        issue_data.append(['', '', ''])
    
    issue_table = Table(issue_data, colWidths=[8*cm, 4*cm, 4.5*cm])
    issue_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(issue_table)
    story.append(Spacer(1, 20))
    
    # 预计交付时间
    expected_date = room_info.get('expected_delivery_date', '')
    if expected_date:
        if isinstance(expected_date, str):
            try:
                date_obj = datetime.fromisoformat(expected_date)
                date_str = date_obj.strftime('%Y年%m月%d日')
            except:
                date_str = expected_date
        else:
            date_str = str(expected_date)
    else:
        date_str = '待定'
    
    delivery_data = [['预计交付时间', date_str, '', '']]
    delivery_table = Table(delivery_data, colWidths=[4*cm, 12.5*cm])
    delivery_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('SPAN', (1, 0), (3, 0)),  # 内容跨列
    ]))
    
    story.append(delivery_table)
    
    # 生成PDF
    try:
        print("开始构建PDF文档...")
        print(f"使用字体: {font_name}")
        doc.build(story)
        buffer.seek(0)
        pdf_data = buffer.read()
        print(f"PDF生成成功，大小: {len(pdf_data)} 字节")
        return pdf_data
    except Exception as e:
        print(f"PDF构建失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 如果使用中文字体失败，尝试使用英文字体重新生成
        if font_name == 'SimHei':
            print("尝试使用Helvetica字体重新生成PDF...")
            try:
                # 重新生成，使用简化的内容和Helvetica字体
                return create_fallback_pdf(
                    room_info, customer_info, communications, 
                    quality_issues, assigned_users, latest_customer_description
                )
            except Exception as fallback_e:
                print(f"使用备用字体也失败: {fallback_e}")
                raise Exception(f"PDF生成失败: 中文字体错误 - {str(e)}, 备用字体错误 - {str(fallback_e)}")
        else:
            raise Exception(f"PDF生成失败: {str(e)}")

def create_fallback_pdf(
    room_info: dict,
    customer_info: Optional[dict],
    communications: List[dict],
    quality_issues: List[dict],
    assigned_users: dict,
    latest_customer_description: str = ""
) -> bytes:
    """使用Helvetica字体生成简化版PDF的备用方案"""
    print("使用备用方案生成PDF...")
    
    # 创建PDF文档
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2*cm,
        bottomMargin=2*cm,
        leftMargin=2*cm,
        rightMargin=2*cm
    )
    
    # 使用简单的样式
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=16,
        alignment=TA_CENTER
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10
    )
    
    # 构建简化的PDF内容
    story = []
    
    # 标题
    title = f"Room Communication Report - {room_info.get('building_unit', '')}{room_info.get('room_number', '')}"
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 20))
    
    # 客户信息
    if customer_info:
        story.append(Paragraph("Customer Information:", normal_style))
        story.append(Paragraph(f"Name: {customer_info.get('name', 'N/A')}", normal_style))
        story.append(Paragraph(f"Phone: {customer_info.get('phone', 'N/A')}", normal_style))
        story.append(Spacer(1, 10))
    
    # 沟通记录
    if communications:
        story.append(Paragraph("Communications:", normal_style))
        for i, comm in enumerate(communications[:5]):  # 限制条数
            content = comm.get('content', 'No content')[:100]  # 限制长度
            story.append(Paragraph(f"{i+1}. {content}", normal_style))
        story.append(Spacer(1, 10))
    
    # 质量问题
    if quality_issues:
        story.append(Paragraph("Quality Issues:", normal_style))
        for i, issue in enumerate(quality_issues[:5]):  # 限制条数
            desc = issue.get('description', 'No description')[:100]  # 限制长度
            story.append(Paragraph(f"{i+1}. {desc}", normal_style))
    
    # 生成PDF
    doc.build(story)
    buffer.seek(0)
    pdf_data = buffer.read()
    print(f"备用PDF生成成功，大小: {len(pdf_data)} 字节")
    return pdf_data