# -*- coding: utf-8 -*-

import datetime
import sys
import os
import io
import time
import unittest
import shutil
import click
import copy
from enum import Enum
from xml.sax import saxutils
from .__init__ import __version__
import traceback


# ----------------------------------------------------------------------
# Template
class HtmlFileTemplate(object):
    """
    Define a HTML template for report customerization and generation.

    Overall structure of an HTML report

    HTML
    +------------------------+
    |<html>                  |
    |  <head>                |
    |                        |
    |   STYLESHEET           |
    |   +----------------+   |
    |   |                |   |
    |   +----------------+   |
    |                        |
    |  </head>               |
    |                        |
    |  <body>                |
    |                        |
    |   HEADING              |
    |   +----------------+   |
    |   |                |   |
    |   +----------------+   |
    |                        |
    |   REPORT               |
    |   +----------------+   |
    |   |                |   |
    |   +----------------+   |
    |                        |
    |   ENDING               |
    |   +----------------+   |
    |   |                |   |
    |   +----------------+   |
    |                        |
    |  </body>               |
    |</html>                 |
    +------------------------+
    """

    STATUS = {
        0: u'通过',
        1: u'失败',
        2: u'错误',
    }

    DEFAULT_TITLE = 'Unit Test Report'
    DEFAULT_DESCRIPTION = ''

    # ------------------------------------------------------------------------
    # HTML Template

    HTML_TMPL = r"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>%(title)s</title>
    <meta name="generator" content="%(generator)s"/>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
    
    <link href="css/bootstrap.min.css" rel="stylesheet">
    <script type="text/javascript" src="js/echarts.common.min.js"></script>
    
    %(stylesheet)s
    
</head>
<body>
    <script language="javascript" type="text/javascript"><!--
    output_list = Array();

    /* level - 0:Summary; 1:Failed; 2:All */
    function showCase(level) {
        trs = document.getElementsByTagName("tr");
        for (var i = 0; i < trs.length; i++) {
            tr = trs[i];
            id = tr.id;
            if (id.substr(0,2) == 'ft') {
                if (level < 1) {
                    tr.className = 'hiddenRow';
                }
                else {
                    tr.className = '';
                }
            }
            if (id.substr(0,2) == 'pt') {
                if (level > 1) {
                    tr.className = '';
                }
                else {
                    tr.className = 'hiddenRow';
                }
            }
        }
    }


    function showClassDetail(cid, count) {
        var id_list = Array(count);
        var toHide = 1;
        for (var i = 0; i < count; i++) {
            tid0 = 't' + cid.substr(1) + '.' + (i+1);
            tid = 'f' + tid0;
            tr = document.getElementById(tid);
            if (!tr) {
                tid = 'p' + tid0;
                tr = document.getElementById(tid);
            }
            id_list[i] = tid;
            if (tr.className) {
                toHide = 0;
            }
        }
        for (var i = 0; i < count; i++) {
            tid = id_list[i];
            if (toHide) {
                document.getElementById('div_'+tid).style.display = 'none'
                document.getElementById(tid).className = 'hiddenRow';
            }
            else {
                document.getElementById(tid).className = '';
            }
        }
    }


    function showTestDetail(div_id){
        var details_div = document.getElementById(div_id)
        var displayState = details_div.style.display
        // alert(displayState)
        if (displayState != 'block' ) {
            displayState = 'block'
            details_div.style.display = 'block'
        }
        else {
            details_div.style.display = 'none'
        }
    }


    function html_escape(s) {
        s = s.replace(/&/g,'&amp;');
        s = s.replace(/</g,'&lt;');
        s = s.replace(/>/g,'&gt;');
        return s;
    }

    /* obsoleted by detail in <div>
    function showOutput(id, name) {
        var w = window.open("", //url
                        name,
                        "resizable,scrollbars,status,width=800,height=450");
        d = w.document;
        d.write("<pre>");
        d.write(html_escape(output_list[id]));
        d.write("\n");
        d.write("<a href='javascript:window.close()'>close</a>\n");
        d.write("</pre>\n");
        d.close();
    }
    */
    --></script>

    <div id="div_base">
        %(heading)s
        %(report)s
        %(ending)s
        %(chart_script)s
    </div>
</body>
</html>
"""  # variables: (title, generator, stylesheet, heading, report, ending, chart_script)

    ECHARTS_SCRIPT = """
    <script type="text/javascript">
        // 基于准备好的dom，初始化echarts实例
        var myChart = echarts.init(document.getElementById('chart'));

        // 指定图表的配置项和数据
        var option = {
            title : {
                text: '测试执行情况',
                x:'center'
            },
            tooltip : {
                trigger: 'item',
                formatter: "{a} <br/>{b} : {c} ({d}%%)"
            },
            color: ['#95b75d', 'grey', '#b64645'],
            legend: {
                orient: 'vertical',
                left: 'left',
                data: ['通过','失败','错误']
            },
            series : [
                {
                    name: '测试执行情况',
                    type: 'pie',
                    radius : '60%%',
                    center: ['50%%', '60%%'],
                    data:[
                        {value:%(Pass)s, name:'通过'},
                        {value:%(fail)s, name:'失败'},
                        {value:%(error)s, name:'错误'}
                    ],
                    itemStyle: {
                        emphasis: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    }
                }
            ]
        };

        // 使用刚指定的配置项和数据显示图表。
        myChart.setOption(option);
    </script>
    """  # variables: (Pass, fail, error)

    # ------------------------------------------------------------------------
    # Stylesheet
    #
    # alternatively use a <link> for external style sheet, e.g.
    #   <link rel="stylesheet" href="$url" type="text/css">

    STYLESHEET_TMPL = """
<style type="text/css" media="screen">
    body        { font-family: Microsoft YaHei,Consolas,arial,sans-serif; font-size: 80%; }
    table       { font-size: 100%; }
    pre         { white-space: pre-wrap;word-wrap: break-word; }

    /* -- heading ---------------------------------------------------------------------- */
    h1 {
        font-size: 16pt;
        color: gray;
    }
    .heading {
        margin-top: 0ex;
        margin-bottom: 1ex;
    }

    .heading .attribute {
        margin-top: 1ex;
        margin-bottom: 0;
    }

    .heading .description {
        margin-top: 2ex;
        margin-bottom: 3ex;
    }

    /* -- css div popup ------------------------------------------------------------------------ */
    a.popup_link {
    }

    a.popup_link:hover {
        color: red;
    }

    .popup_window {
        display: none;
        position: relative;
        left: 0px;
        top: 0px;
        /*border: solid #627173 1px; */
        padding: 10px;
        /*background-color: #E6E6D6; */
        font-family: "Lucida Console", "Courier New", Courier, monospace;
        text-align: left;
        font-size: 8pt;
        /* width: 500px;*/
    }

    }
    /* -- report ------------------------------------------------------------------------ */
    #show_detail_line {
        margin-top: 3ex;
        margin-bottom: 1ex;
    }
    #result_table {
        width: 99%;
    }
    #header_row {
        font-weight: bold;
        color: #303641;
        background-color: #ebebeb;
    }
    #total_row  { font-weight: bold; }
    .passClass  { background-color: #bdedbc; }
    .failClass  { background-color: #ffefa4; }
    .errorClass { background-color: #ffc9c9; }
    .passCase   { color: #6c6; }
    .failCase   { color: #FF6600; font-weight: bold; }
    .errorCase  { color: #c00; font-weight: bold; }
    .hiddenRow  { display: none; }
    .testcase   { margin-left: 2em; }


    /* -- ending ---------------------------------------------------------------------- */
    #ending {
    }

    #div_base {
                position:absolute;
                top:0%;
                left:5%;
                right:5%;
                width: auto;
                height: auto;
                margin: -15px 0 0 0;
    }
</style>
"""

    # ------------------------------------------------------------------------
    # Heading
    #

    HEADING_TMPL = """
    <div class='page-header'>
        <h1>%(title)s</h1>
    %(parameters)s
    </div>
    <div style="float: left;width:50%%;"><p class='description'>%(description)s</p></div>
    <div id="chart" style="width:50%%;height:400px;float:left;"></div>
"""  # variables: (title, parameters, description)

    HEADING_ATTRIBUTE_TMPL = """<p class='attribute'><strong>%(name)s:</strong> %(value)s</p>
"""  # variables: (name, value)

    # ------------------------------------------------------------------------
    # Report
    #

    REPORT_TMPL = u"""
    <div class="btn-group btn-group-sm">
        <button class="btn btn-default" onclick='javascript:showCase(0)'>总结</button>
        <button class="btn btn-default" onclick='javascript:showCase(1)'>失败</button>
        <button class="btn btn-default" onclick='javascript:showCase(2)'>全部</button>
    </div>
    <p></p>
    <table id='result_table' class="table table-bordered">
        <colgroup>
            <col align='left' />
            <col align='right' />
            <col align='right' />
            <col align='right' />
            <col align='right' />
            <col align='right' />
        </colgroup>
        <tr id='header_row'>
            <td>测试套件/测试用例</td>
            <td>总数</td>
            <td>通过</td>
            <td>失败</td>
            <td>错误</td>
            <td>查看</td>
        </tr>
        %(test_list)s
        <tr id='total_row'>
            <td>总计</td>
            <td>%(count)s</td>
            <td>%(Pass)s</td>
            <td>%(fail)s</td>
            <td>%(error)s</td>
            <td>&nbsp;</td>
        </tr>
    </table>
"""  # variables: (test_list, count, Pass, fail, error)

    REPORT_CLASS_TMPL = u"""
    <tr class='%(style)s'>
        <td>%(desc)s</td>
        <td>%(count)s</td>
        <td>%(Pass)s</td>
        <td>%(fail)s</td>
        <td>%(error)s</td>
        <td><a href="javascript:showClassDetail('%(cid)s',%(count)s)">详情</a></td>
    </tr>
"""  # variables: (style, desc, count, Pass, fail, error, cid)

    REPORT_TEST_WITH_OUTPUT_TMPL = r"""
<tr id='%(tid)s' class='%(Class)s'>
    <td class='%(style)s'><div class='testcase'>%(desc)s</div></td>
    <td colspan='5' align='center'>

    <!--css div popup start-->
    <a class="popup_link" onfocus='this.blur();' href="javascript:showTestDetail('div_%(tid)s')" >
        %(status)s</a>

    <div id='div_%(tid)s' class="popup_window">
        <pre>%(script)s</pre>
    </div>
    <!--css div popup end-->

    </td>
</tr>
"""  # variables: (tid, Class, style, desc, status)

    REPORT_TEST_NO_OUTPUT_TMPL = r"""
<tr id='%(tid)s' class='%(Class)s'>
    <td class='%(style)s'><div class='testcase'>%(desc)s</div></td>
    <td colspan='5' align='center'>%(status)s</td>
</tr>
"""  # variables: (tid, Class, style, desc, status)

    REPORT_TEST_OUTPUT_TMPL = r"""%(id)s: %(output)s"""  # variables: (id, output)

    # ------------------------------------------------------------------------
    # ENDING
    #

    ENDING_TMPL = """<div id='ending'>&nbsp;</div>"""


# -------------------- The end of the Template class -------------------


class TestCaseStatus(Enum):
    UNKNOWN = 0
    SUCCESS = 1
    FAILURE = 2
    ERROR = 3


class TestCase(object):
    def __init__(self):
        self.CaseName = None
        self.CaseStatus = TestCaseStatus.UNKNOWN
        self.CaseDescription = ""
        self.ErrorStackTrace = ""
        # tid 命名方法：  pt%d%d     成功Case
        # tid 命名方法：  ft%d%d     失败Case  %suiteid.%caseid
        self.tid = ""        # case id

    def getCaseName(self):
        return self.CaseName

    def setCaseName(self, p_CaseName):
        self.CaseName = p_CaseName

    def setCaseStatus(self, p_CaseStatus):
        self.CaseStatus = p_CaseStatus

    def getCaseStatus(self):
        return self.CaseStatus

    def getCaseDescription(self):
        return self.CaseDescription

    def getErrorStackTrace(self):
        return self.ErrorStackTrace

    def setErrorStackTrace(self, p_ErrorStackTrace):
        self.ErrorStackTrace = p_ErrorStackTrace

    def setTID(self, p_TID):
        self.tid = p_TID

    def getTID(self):
        return self.tid


class TestSuite(object):
    def __init__(self):
        self.SuiteName = None
        self.TestCases = []
        self.SuiteDescription = ""
        self.PassedCaseCount = 0
        self.FailedCaseCount = 0
        self.ErrorCaseCount = 0
        self.sid = 0
        self.max_tid = 1

    def getSuiteName(self):
        return self.SuiteName

    def setSuiteName(self, p_SuiteName):
        self.SuiteName = p_SuiteName

    def addTestCase(self, p_TestCase):
        if p_TestCase.getCaseStatus() == TestCaseStatus.SUCCESS:
            self.PassedCaseCount = self.PassedCaseCount + 1
        if p_TestCase.getCaseStatus() == TestCaseStatus.FAILURE:
            self.FailedCaseCount = self.FailedCaseCount + 1
        if p_TestCase.getCaseStatus() == TestCaseStatus.ERROR:
            self.ErrorCaseCount = self.ErrorCaseCount + 1
        m_TestCase = copy.copy(p_TestCase)
        m_TestCase.setTID(self.max_tid)
        self.max_tid = self.max_tid + 1
        self.TestCases.append(m_TestCase)

    def getSuiteStatus(self):
        return self.SuiteStatus

    def setSuiteStatus(self, p_SuiteStatus):
        self.SuiteStatus = p_SuiteStatus

    def getSuiteDescription(self):
        return self.SuiteDescription

    def setSuiteDescription(self, p_SuiteDescription):
        self.SuiteDescription = p_SuiteDescription

    def getPassedCaseCount(self):
        return self.PassedCaseCount

    def getFailedCaseCount(self):
        return self.FailedCaseCount

    def getErrorCaseCount(self):
        return self.ErrorCaseCount

    def setSID(self, p_SID):
        self.sid = p_SID

    def getSID(self):
        return self.sid


class TestResult(object):
    # note: _TestResult is a pure representation of results.
    # It lacks the output and reporting ability compares to unittest._TextTestResult.

    def __init__(self):
        self.TestResults = []
        self.success_count = 0
        self.failure_count = 0
        self.error_count = 0
        self.max_sid = 1

    def addSuite(self, p_TestSuite):
        # 更新TestResult的全局统计信息
        self.success_count = self.success_count + p_TestSuite.PassedCaseCount
        self.failure_count = self.failure_count + p_TestSuite.FailedCaseCount
        self.error_count = self.error_count + p_TestSuite.ErrorCaseCount

        m_TestSuite = copy.copy(p_TestSuite)
        m_TestSuite.setSID(self.max_sid)
        self.max_sid = self.max_sid + 1
        self.TestResults.append(m_TestSuite)


class HTMLTestRunner(HtmlFileTemplate):

    def __init__(self, verbosity=1, title=None, description=None):
        self.verbosity = verbosity
        self.stopTime = 0

        if title is None:
            self.title = self.DEFAULT_TITLE
        else:
            self.title = title
        if description is None:
            self.description = self.DEFAULT_DESCRIPTION
        else:
            self.description = description

        self.startTime = datetime.datetime.now()
        self.stopTime = datetime.datetime.now()

    def getReportAttributes(self, result):
        """
        Return report attributes as a list of (name, value).
        Override this to add custom attributes.
        """
        startTime = str(self.startTime)[:19]
        duration = str(self.stopTime - self.startTime)
        status = []
        if result.success_count: status.append(u'通过 %s' % result.success_count)
        if result.failure_count: status.append(u'失败 %s' % result.failure_count)
        if result.error_count:   status.append(u'错误 %s' % result.error_count)
        if status:
            status = ' '.join(status)
        else:
            status = 'none'
        return [
            (u'开始时间', startTime),
            (u'运行时长', duration),
            (u'状态', status),
        ]

    def generateReport(self, result, p_output):
        report_attrs = self.getReportAttributes(result)
        generator = 'HTMLTestRunner %s' % __version__
        stylesheet = self._generate_stylesheet()
        heading = self._generate_heading(report_attrs)
        report = self._generate_report(result)
        ending = self._generate_ending()
        chart = self._generate_chart(result)
        output = self.HTML_TMPL % dict(
            title=saxutils.escape(self.title),
            generator=generator,
            stylesheet=stylesheet,
            heading=heading,
            report=report,
            ending=ending,
            chart_script=chart
        )
        # 生成html文件
        m_OutputHandler = open(p_output, "w", encoding='utf8')
        m_OutputHandler.write(output)
        m_OutputHandler.close()

        # 复制需要的css和js文件
        m_csspath = os.path.abspath(os.path.join(os.path.dirname(__file__), "css"))
        m_jspath = os.path.abspath(os.path.join(os.path.dirname(__file__), "js"))
        m_new_csspath = os.path.abspath(os.path.join(os.path.dirname(p_output), "css"))
        m_new_jspath = os.path.abspath(os.path.join(os.path.dirname(p_output), "js"))
        print(m_csspath)
        print(m_jspath)
        print(m_new_csspath)
        print(m_new_jspath)
        if m_csspath != m_new_csspath:
            if os.path.exists(m_new_csspath):
                shutil.rmtree(m_new_csspath)
            os.makedirs(m_new_csspath)
            shutil.copytree(m_csspath, m_new_csspath)
        if m_jspath != m_new_jspath:
            if os.path.exists(m_new_jspath):
                shutil.rmtree(m_new_jspath)
            os.makedirs(m_new_jspath)
            shutil.copytree(m_jspath, m_new_jspath)

    def _generate_stylesheet(self):
        return self.STYLESHEET_TMPL

    def _generate_heading(self, report_attrs):
        a_lines = []
        for name, value in report_attrs:
            line = self.HEADING_ATTRIBUTE_TMPL % dict(
                name=saxutils.escape(name),
                value=saxutils.escape(value),
            )
            a_lines.append(line)
        heading = self.HEADING_TMPL % dict(
            title=saxutils.escape(self.title),
            parameters=''.join(a_lines),
            description=saxutils.escape(self.description),
        )
        return heading

    def _generate_report(self, result):
        rows = []
        nPos = 1
        for m_TestSuite in result.TestResults:
            m_TestSuite.setSID(nPos)
            nPos = nPos + 1
            if len(m_TestSuite.getSuiteDescription()) == 0:
                desc = m_TestSuite.getSuiteName()
            else:
                desc = m_TestSuite.getSuiteDescription()

            if m_TestSuite.getErrorCaseCount() > 0:
                m_CSSStype = "errorClass"
            elif m_TestSuite.getFailedCaseCount() > 0:
                m_CSSStype = "failClass"
            else:
                m_CSSStype = "passClass"
            m_TotalCaseCount = m_TestSuite.getPassedCaseCount() + \
                               m_TestSuite.getFailedCaseCount() + \
                               m_TestSuite.getErrorCaseCount()
            row = self.REPORT_CLASS_TMPL % dict(
                style=m_CSSStype,
                desc=desc,
                count=m_TotalCaseCount,
                Pass=m_TestSuite.getPassedCaseCount(),
                fail=m_TestSuite.getFailedCaseCount(),
                error=m_TestSuite.getErrorCaseCount(),
                cid="c" + str(m_TestSuite.getSID()),
            )
            rows.append(row)

            # 生成Suite下面TestCase的详细内容
            for m_TestCase in m_TestSuite.TestCases:
                self._generate_report_test(rows, m_TestSuite.getSID(), m_TestCase)

        report = self.REPORT_TMPL % dict(
            test_list=''.join(rows),
            count=str(result.success_count + result.failure_count + result.error_count),
            Pass=str(result.success_count),
            fail=str(result.failure_count),
            error=str(result.error_count),
        )
        return report

    def _generate_chart(self, result):
        chart = self.ECHARTS_SCRIPT % dict(
            Pass=str(result.success_count),
            fail=str(result.failure_count),
            error=str(result.error_count),
        )
        return chart

    def _generate_report_test(self, rows, cid, p_TestCase):
        has_output = True
        if p_TestCase.getCaseStatus() == TestCaseStatus.SUCCESS:
            tid = "pt" + str(cid) + "." + str(p_TestCase.getTID())
            m_Status = "通过"
        elif p_TestCase.getCaseStatus() == TestCaseStatus.FAILURE:
            tid = "ft" + str(cid) + "." + str(p_TestCase.getTID())
            m_Status = "失败"
        else:
            tid = "ft" + str(cid) + "." + str(p_TestCase.getTID())
            m_Status = "错误"

        if len(p_TestCase.getCaseDescription()) == 0:
            desc = p_TestCase.getCaseName()
        else:
            desc = p_TestCase.getCaseDescription()
        tmpl = has_output and self.REPORT_TEST_WITH_OUTPUT_TMPL or self.REPORT_TEST_NO_OUTPUT_TMPL

        script = self.REPORT_TEST_OUTPUT_TMPL % dict(
            id=tid,
            output=saxutils.escape(p_TestCase.getErrorStackTrace()),
        )

        if p_TestCase.getCaseStatus() == TestCaseStatus.SUCCESS:
            m_CSS_CaseStyle = "none"
        elif p_TestCase.getCaseStatus() == TestCaseStatus.FAILURE:
            m_CSS_CaseStyle = "failCase"
        else:
            m_CSS_CaseStyle = "errorCase"
        row = tmpl % dict(
            tid=tid,
            Class='hiddenRow',
            style=m_CSS_CaseStyle,
            desc=desc,
            script=script,
            status=m_Status,
        )
        rows.append(row)
        if not has_output:
            return

    def _generate_ending(self):
        return self.ENDING_TMPL


@click.command()
@click.option("--version", is_flag=True, help="Output HtmlTestReport version.")
@click.option("--output", type=str, required=True, help="Output Html Report.")
def GenerateHtmlTestReport(
        version,
        output
):
    if version:
        print("Version:", __version__)
        sys.exit(0)
    m_OutputFileName = output
    m_HTMLTestRunner = HTMLTestRunner(verbosity=1, title="回归测试报告")

    m_Suite1 = TestSuite()
    m_Suite1.setSuiteName("测试套件一")

    m_Case1 = TestCase()
    m_Case1.setCaseName("测试名称1")
    m_Case1.setCaseStatus(TestCaseStatus.SUCCESS)
    m_Case1.setErrorStackTrace("错误信息对战")

    m_Case2 = TestCase()
    m_Case2.setCaseName("测试名称2")
    m_Case2.setCaseStatus(TestCaseStatus.SUCCESS)
    m_Case2.setErrorStackTrace("小雪是美女")

    m_Case3 = TestCase()
    m_Case3.setCaseName("测试名称3")
    m_Case3.setCaseStatus(TestCaseStatus.FAILURE)
    m_Case3.setErrorStackTrace("金正恩是帅哥")

    m_Suite1.addTestCase(m_Case1)
    m_Suite1.addTestCase(m_Case2)
    m_Suite1.addTestCase(m_Case3)

    m_TestResult = TestResult()
    m_TestResult.addSuite(m_Suite1)

    m_HTMLTestRunner.generateReport(result=m_TestResult, p_output=m_OutputFileName)


if __name__ == "__main__":
    try:
        GenerateHtmlTestReport()
    except Exception as ge:
        print('traceback.print_exc():\n%s' % traceback.print_exc())
        print('traceback.format_exc():\n%s' % traceback.format_exc())
        print("Fatal Exception: " + repr(ge))
