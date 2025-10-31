import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, AreaChart, Area, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Types
interface Report {
  id: string;
  name: string;
  description?: string;
  report_type: string;
  config: any;
  date_range_type: string;
  custom_start_date?: string;
  custom_end_date?: string;
  compare_enabled: boolean;
  compare_period?: string;
  last_run_at?: string;
  created_at: string;
}

interface ReportExecution {
  id: string;
  report_id: string;
  executed_at: string;
  execution_time_ms: number;
  start_date: string;
  end_date: string;
  results_data: any;
  comparison_data?: any;
  status: string;
}

interface QuickReportRequest {
  report_type: string;
  date_range_type: string;
  custom_start_date?: string;
  custom_end_date?: string;
  compare_enabled: boolean;
  compare_period?: string;
}

const REPORT_TYPES = [
  { value: 'campaign_performance', label: '캠페인 성과' },
  { value: 'channel_comparison', label: '채널 비교' },
  { value: 'lead_analytics', label: '리드 분석' },
  { value: 'engagement_metrics', label: '참여도 지표' },
  { value: 'roi_analysis', label: 'ROI 분석' },
  { value: 'conversion_funnel', label: '전환 퍼널' },
];

const DATE_RANGE_TYPES = [
  { value: 'today', label: '오늘' },
  { value: 'yesterday', label: '어제' },
  { value: 'last_7_days', label: '최근 7일' },
  { value: 'last_30_days', label: '최근 30일' },
  { value: 'last_90_days', label: '최근 90일' },
  { value: 'this_month', label: '이번 달' },
  { value: 'last_month', label: '지난 달' },
  { value: 'this_year', label: '올해' },
  { value: 'custom', label: '사용자 지정' },
];

const COMPARE_PERIODS = [
  { value: 'previous_period', label: '이전 기간' },
  { value: 'previous_month', label: '이전 달' },
  { value: 'previous_year', label: '작년 동기' },
];

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1'];

const Reports: React.FC = () => {
  const [reports, setReports] = useState<Report[]>([]);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [currentExecution, setCurrentExecution] = useState<ReportExecution | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'quick' | 'saved'>('quick');

  // Quick report form state
  const [quickReportType, setQuickReportType] = useState('campaign_performance');
  const [dateRangeType, setDateRangeType] = useState('last_30_days');
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [compareEnabled, setCompareEnabled] = useState(false);
  const [comparePeriod, setComparePeriod] = useState('previous_period');

  // New report modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newReportName, setNewReportName] = useState('');
  const [newReportDescription, setNewReportDescription] = useState('');
  const [newReportType, setNewReportType] = useState('campaign_performance');

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/reports/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setReports(data);
      }
    } catch (error) {
      console.error('Failed to fetch reports:', error);
    }
  };

  const generateQuickReport = async () => {
    setLoading(true);
    try {
      const requestData: QuickReportRequest = {
        report_type: quickReportType,
        date_range_type: dateRangeType,
        compare_enabled: compareEnabled,
        compare_period: compareEnabled ? comparePeriod : undefined,
      };

      if (dateRangeType === 'custom') {
        requestData.custom_start_date = customStartDate;
        requestData.custom_end_date = customEndDate;
      }

      const response = await fetch('http://localhost:8000/api/reports/quick-report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(requestData),
      });

      if (response.ok) {
        const execution = await response.json();
        setCurrentExecution(execution);
        setSelectedReport(null);
      }
    } catch (error) {
      console.error('Failed to generate quick report:', error);
    } finally {
      setLoading(false);
    }
  };

  const createReport = async () => {
    if (!newReportName.trim()) return;

    try {
      const response = await fetch('http://localhost:8000/api/reports/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          name: newReportName,
          description: newReportDescription,
          report_type: newReportType,
          config: {},
          date_range_type: dateRangeType,
          custom_start_date: dateRangeType === 'custom' ? customStartDate : undefined,
          custom_end_date: dateRangeType === 'custom' ? customEndDate : undefined,
          compare_enabled: compareEnabled,
          compare_period: compareEnabled ? comparePeriod : undefined,
        }),
      });

      if (response.ok) {
        await fetchReports();
        setShowCreateModal(false);
        setNewReportName('');
        setNewReportDescription('');
        setNewReportType('campaign_performance');
      }
    } catch (error) {
      console.error('Failed to create report:', error);
    }
  };

  const runSavedReport = async (reportId: string) => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/reports/${reportId}/run`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const execution = await response.json();
        setCurrentExecution(execution);
      }
    } catch (error) {
      console.error('Failed to run report:', error);
    } finally {
      setLoading(false);
    }
  };

  const deleteReport = async (reportId: string) => {
    if (!confirm('이 리포트를 삭제하시겠습니까?')) return;

    try {
      const response = await fetch(`http://localhost:8000/api/reports/${reportId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        await fetchReports();
        if (selectedReport?.id === reportId) {
          setSelectedReport(null);
          setCurrentExecution(null);
        }
      }
    } catch (error) {
      console.error('Failed to delete report:', error);
    }
  };

  const renderCampaignPerformanceChart = (data: any) => {
    if (!data.campaigns || data.campaigns.length === 0) {
      return <p className="text-gray-500 text-center py-8">데이터가 없습니다</p>;
    }

    const chartData = data.campaigns.map((campaign: any) => ({
      name: campaign.name,
      opened: campaign.opened,
      clicked: campaign.clicked,
      sent: campaign.sent,
    }));

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <p className="text-sm text-gray-600">총 발송</p>
            <p className="text-2xl font-bold text-blue-600">{data.total_sent.toLocaleString()}</p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <p className="text-sm text-gray-600">평균 열람률</p>
            <p className="text-2xl font-bold text-green-600">{data.avg_open_rate.toFixed(1)}%</p>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg">
            <p className="text-sm text-gray-600">평균 클릭률</p>
            <p className="text-2xl font-bold text-purple-600">{data.avg_click_rate.toFixed(1)}%</p>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="sent" fill="#8884d8" name="발송" />
            <Bar dataKey="opened" fill="#82ca9d" name="열람" />
            <Bar dataKey="clicked" fill="#ffc658" name="클릭" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  };

  const renderChannelComparisonChart = (data: any) => {
    const channels = data.channels || [];
    if (channels.length === 0) {
      return <p className="text-gray-500 text-center py-8">데이터가 없습니다</p>;
    }

    return (
      <div className="space-y-6">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={channels}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="channel" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="sent" fill="#8884d8" name="발송" />
            <Bar dataKey="opened" fill="#82ca9d" name="열람" />
            <Bar dataKey="clicked" fill="#ffc658" name="클릭" />
          </BarChart>
        </ResponsiveContainer>

        <div className="grid grid-cols-3 gap-4">
          {channels.map((channel: any, index: number) => (
            <div key={channel.channel} className="bg-gray-50 p-4 rounded-lg">
              <p className="font-semibold text-lg mb-2">{channel.channel}</p>
              <div className="space-y-1 text-sm">
                <p>발송: {channel.sent.toLocaleString()}</p>
                <p>열람률: {channel.open_rate.toFixed(1)}%</p>
                <p>클릭률: {channel.click_rate.toFixed(1)}%</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderLeadAnalyticsChart = (data: any) => {
    const statusData = Object.entries(data.by_status || {}).map(([status, count]) => ({
      name: status,
      value: count as number,
    }));

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <p className="text-sm text-gray-600">신규 리드</p>
            <p className="text-2xl font-bold text-blue-600">{data.new_leads.toLocaleString()}</p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <p className="text-sm text-gray-600">총 리드</p>
            <p className="text-2xl font-bold text-green-600">{data.total_leads.toLocaleString()}</p>
          </div>
        </div>

        {statusData.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold mb-4">리드 상태 분포</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: ${entry.value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {statusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    );
  };

  const renderEngagementMetricsChart = (data: any) => {
    const timeline = data.timeline || [];
    if (timeline.length === 0) {
      return <p className="text-gray-500 text-center py-8">데이터가 없습니다</p>;
    }

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <p className="text-sm text-gray-600">평균 열람률</p>
            <p className="text-2xl font-bold text-blue-600">{data.avg_open_rate.toFixed(1)}%</p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <p className="text-sm text-gray-600">평균 클릭률</p>
            <p className="text-2xl font-bold text-green-600">{data.avg_click_rate.toFixed(1)}%</p>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={timeline}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Area type="monotone" dataKey="open_rate" stackId="1" stroke="#8884d8" fill="#8884d8" name="열람률" />
            <Area type="monotone" dataKey="click_rate" stackId="2" stroke="#82ca9d" fill="#82ca9d" name="클릭률" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    );
  };

  const renderReportResults = (execution: ReportExecution) => {
    if (!execution) return null;

    const data = execution.results_data;
    const reportType = quickReportType || selectedReport?.report_type;

    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-bold mb-2">리포트 결과</h2>
          <p className="text-sm text-gray-600">
            기간: {new Date(execution.start_date).toLocaleDateString()} - {new Date(execution.end_date).toLocaleDateString()}
          </p>
          <p className="text-sm text-gray-600">
            생성 시간: {new Date(execution.executed_at).toLocaleString()} (실행 시간: {execution.execution_time_ms}ms)
          </p>
        </div>

        {reportType === 'campaign_performance' && renderCampaignPerformanceChart(data)}
        {reportType === 'channel_comparison' && renderChannelComparisonChart(data)}
        {reportType === 'lead_analytics' && renderLeadAnalyticsChart(data)}
        {reportType === 'engagement_metrics' && renderEngagementMetricsChart(data)}

        {execution.comparison_data && (
          <div className="mt-8 pt-6 border-t">
            <h3 className="text-lg font-semibold mb-4">비교 기간 데이터</h3>
            <div className="bg-gray-50 p-4 rounded">
              <pre className="text-sm overflow-auto">{JSON.stringify(execution.comparison_data, null, 2)}</pre>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">고급 리포팅</h1>
        <p className="text-gray-600 mt-2">마케팅 성과를 분석하고 데이터 기반 인사이트를 확인하세요</p>
      </div>

      {/* Tabs */}
      <div className="flex border-b mb-6">
        <button
          onClick={() => setActiveTab('quick')}
          className={`px-6 py-3 font-medium ${
            activeTab === 'quick'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          빠른 리포트
        </button>
        <button
          onClick={() => setActiveTab('saved')}
          className={`px-6 py-3 font-medium ${
            activeTab === 'saved'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          저장된 리포트
        </button>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Left Panel - Configuration */}
        <div className="col-span-1 space-y-4">
          {activeTab === 'quick' ? (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold mb-4">빠른 리포트 생성</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    리포트 유형
                  </label>
                  <select
                    value={quickReportType}
                    onChange={(e) => setQuickReportType(e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {REPORT_TYPES.map((type) => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    기간
                  </label>
                  <select
                    value={dateRangeType}
                    onChange={(e) => setDateRangeType(e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {DATE_RANGE_TYPES.map((type) => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                </div>

                {dateRangeType === 'custom' && (
                  <div className="space-y-2">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        시작일
                      </label>
                      <input
                        type="date"
                        value={customStartDate}
                        onChange={(e) => setCustomStartDate(e.target.value)}
                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        종료일
                      </label>
                      <input
                        type="date"
                        value={customEndDate}
                        onChange={(e) => setCustomEndDate(e.target.value)}
                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                )}

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="compare"
                    checked={compareEnabled}
                    onChange={(e) => setCompareEnabled(e.target.checked)}
                    className="mr-2"
                  />
                  <label htmlFor="compare" className="text-sm font-medium text-gray-700">
                    이전 기간과 비교
                  </label>
                </div>

                {compareEnabled && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      비교 기간
                    </label>
                    <select
                      value={comparePeriod}
                      onChange={(e) => setComparePeriod(e.target.value)}
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {COMPARE_PERIODS.map((period) => (
                        <option key={period.value} value={period.value}>
                          {period.label}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <button
                  onClick={generateQuickReport}
                  disabled={loading}
                  className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {loading ? '생성 중...' : '리포트 생성'}
                </button>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">저장된 리포트</h2>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm"
                >
                  + 새 리포트
                </button>
              </div>

              <div className="space-y-2">
                {reports.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">저장된 리포트가 없습니다</p>
                ) : (
                  reports.map((report) => (
                    <div
                      key={report.id}
                      className={`p-4 border rounded-lg cursor-pointer hover:bg-gray-50 ${
                        selectedReport?.id === report.id ? 'border-blue-500 bg-blue-50' : ''
                      }`}
                      onClick={() => setSelectedReport(report)}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="font-semibold">{report.name}</h3>
                          {report.description && (
                            <p className="text-sm text-gray-600">{report.description}</p>
                          )}
                          <p className="text-xs text-gray-500 mt-1">
                            {REPORT_TYPES.find((t) => t.value === report.report_type)?.label}
                          </p>
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              runSavedReport(report.id);
                            }}
                            className="text-blue-600 hover:text-blue-800 text-sm"
                          >
                            실행
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              deleteReport(report.id);
                            }}
                            className="text-red-600 hover:text-red-800 text-sm"
                          >
                            삭제
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right Panel - Results */}
        <div className="col-span-2">
          {currentExecution ? (
            renderReportResults(currentExecution)
          ) : (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-center py-12">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900">리포트 없음</h3>
                <p className="mt-1 text-sm text-gray-500">
                  왼쪽에서 리포트를 생성하거나 선택하세요
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Create Report Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-md w-full">
            <h2 className="text-2xl font-bold mb-4">새 리포트 생성</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  리포트 이름 *
                </label>
                <input
                  type="text"
                  value={newReportName}
                  onChange={(e) => setNewReportName(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="예: 월간 캠페인 성과"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  설명
                </label>
                <textarea
                  value={newReportDescription}
                  onChange={(e) => setNewReportDescription(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder="리포트 설명을 입력하세요"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  리포트 유형 *
                </label>
                <select
                  value={newReportType}
                  onChange={(e) => setNewReportType(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {REPORT_TYPES.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex space-x-3 mt-6">
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setNewReportName('');
                    setNewReportDescription('');
                  }}
                  className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
                >
                  취소
                </button>
                <button
                  onClick={createReport}
                  disabled={!newReportName.trim()}
                  className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                >
                  생성
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Reports;
