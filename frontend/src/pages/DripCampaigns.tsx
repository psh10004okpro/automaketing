import React, { useState, useEffect } from 'react';
import { dripCampaignAPI } from '../services/api';

interface DripCampaign {
  id: string;
  name: string;
  description?: string;
  status: 'draft' | 'active' | 'paused' | 'completed';
  trigger_type: string;
  goal?: string;
  total_steps: number;
  total_subscribers: number;
  active_subscribers: number;
  completed_subscribers: number;
  total_sent: number;
  total_delivered: number;
  total_opens: number;
  total_clicks: number;
  created_at: string;
  started_at?: string;
  steps: DripStep[];
}

interface DripStep {
  id: string;
  campaign_id: string;
  step_order: number;
  name: string;
  message_type: 'email' | 'sms';
  content: string;
  delay_days: number;
  delay_hours: number;
  delay_minutes: number;
  subject?: string;
  from_name?: string;
  cta_text?: string;
  cta_url?: string;
  condition_type: string;
  sent_count: number;
  delivered_count: number;
  opened_count: number;
  clicked_count: number;
}

export default function DripCampaigns() {
  const [campaigns, setCampaigns] = useState<DripCampaign[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState<DripCampaign | null>(null);
  const [showCampaignModal, setShowCampaignModal] = useState(false);
  const [showStepModal, setShowStepModal] = useState(false);
  const [editingStep, setEditingStep] = useState<DripStep | null>(null);
  const [loading, setLoading] = useState(false);

  const [campaignForm, setCampaignForm] = useState({
    name: '',
    description: '',
    trigger_type: 'manual',
    goal: '',
  });

  const [stepForm, setStepForm] = useState({
    name: '',
    message_type: 'email' as 'email' | 'sms',
    content: '',
    delay_days: 0,
    delay_hours: 0,
    delay_minutes: 0,
    subject: '',
    from_name: '',
    cta_text: '',
    cta_url: '',
    condition_type: 'always',
  });

  useEffect(() => {
    loadCampaigns();
  }, []);

  const loadCampaigns = async () => {
    setLoading(true);
    try {
      const response = await dripCampaignAPI.list();
      setCampaigns(response.data);
    } catch (error) {
      console.error('Failed to load drip campaigns:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCampaign = async (id: string) => {
    try {
      const response = await dripCampaignAPI.get(id);
      setSelectedCampaign(response.data);
    } catch (error) {
      console.error('Failed to load campaign:', error);
    }
  };

  const handleCreateCampaign = async () => {
    if (!campaignForm.name) {
      alert('캠페인 이름을 입력해주세요');
      return;
    }

    try {
      await dripCampaignAPI.create(campaignForm);
      alert('드립 캠페인이 생성되었습니다!');
      setShowCampaignModal(false);
      resetCampaignForm();
      loadCampaigns();
    } catch (error) {
      console.error('Failed to create campaign:', error);
      alert('캠페인 생성에 실패했습니다');
    }
  };

  const handleAddStep = async () => {
    if (!selectedCampaign || !stepForm.name || !stepForm.content) {
      alert('필수 항목을 모두 입력해주세요');
      return;
    }

    try {
      if (editingStep) {
        // Update existing step
        await dripCampaignAPI.updateStep(editingStep.id, stepForm);
        alert('스텝이 수정되었습니다!');
      } else {
        // Add new step
        await dripCampaignAPI.addStep(selectedCampaign.id, stepForm);
        alert('스텝이 추가되었습니다!');
      }

      setShowStepModal(false);
      resetStepForm();
      setEditingStep(null);
      loadCampaign(selectedCampaign.id);
    } catch (error) {
      console.error('Failed to add/update step:', error);
      alert('스텝 저장에 실패했습니다');
    }
  };

  const handleDeleteStep = async (stepId: string) => {
    if (!confirm('이 스텝을 삭제하시겠습니까?')) return;

    try {
      await dripCampaignAPI.deleteStep(stepId);
      alert('스텝이 삭제되었습니다');
      if (selectedCampaign) {
        loadCampaign(selectedCampaign.id);
      }
    } catch (error) {
      console.error('Failed to delete step:', error);
      alert('스텝 삭제에 실패했습니다');
    }
  };

  const handleActivateCampaign = async () => {
    if (!selectedCampaign) return;

    if (!confirm('캠페인을 활성화하시겠습니까? 활성화 후 구독자가 자동으로 메시지를 받게 됩니다.')) {
      return;
    }

    try {
      await dripCampaignAPI.activate(selectedCampaign.id);
      alert('캠페인이 활성화되었습니다!');
      loadCampaign(selectedCampaign.id);
      loadCampaigns();
    } catch (error: any) {
      console.error('Failed to activate campaign:', error);
      alert(error.response?.data?.detail || '캠페인 활성화에 실패했습니다');
    }
  };

  const handlePauseCampaign = async () => {
    if (!selectedCampaign) return;

    try {
      await dripCampaignAPI.pause(selectedCampaign.id);
      alert('캠페인이 일시정지되었습니다');
      loadCampaign(selectedCampaign.id);
      loadCampaigns();
    } catch (error) {
      console.error('Failed to pause campaign:', error);
      alert('캠페인 일시정지에 실패했습니다');
    }
  };

  const resetCampaignForm = () => {
    setCampaignForm({
      name: '',
      description: '',
      trigger_type: 'manual',
      goal: '',
    });
  };

  const resetStepForm = () => {
    setStepForm({
      name: '',
      message_type: 'email',
      content: '',
      delay_days: 0,
      delay_hours: 0,
      delay_minutes: 0,
      subject: '',
      from_name: '',
      cta_text: '',
      cta_url: '',
      condition_type: 'always',
    });
  };

  const openEditStep = (step: DripStep) => {
    setEditingStep(step);
    setStepForm({
      name: step.name,
      message_type: step.message_type,
      content: step.content,
      delay_days: step.delay_days,
      delay_hours: step.delay_hours,
      delay_minutes: step.delay_minutes,
      subject: step.subject || '',
      from_name: step.from_name || '',
      cta_text: step.cta_text || '',
      cta_url: step.cta_url || '',
      condition_type: step.condition_type,
    });
    setShowStepModal(true);
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      draft: 'bg-gray-200 text-gray-800',
      active: 'bg-green-200 text-green-800',
      paused: 'bg-yellow-200 text-yellow-800',
      completed: 'bg-blue-200 text-blue-800',
    };
    return badges[status as keyof typeof badges] || badges.draft;
  };

  const getTotalDelay = (step: DripStep) => {
    const parts = [];
    if (step.delay_days > 0) parts.push(`${step.delay_days}일`);
    if (step.delay_hours > 0) parts.push(`${step.delay_hours}시간`);
    if (step.delay_minutes > 0) parts.push(`${step.delay_minutes}분`);
    return parts.length > 0 ? parts.join(' ') : '즉시';
  };

  return (
    <div className="p-6">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">드립 캠페인</h1>
          <p className="text-gray-600 mt-2">
            자동화된 이메일/SMS 시퀀스로 리드를 육성하세요
          </p>
        </div>
        <button
          onClick={() => setShowCampaignModal(true)}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          + 새 드립 캠페인
        </button>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Campaign List */}
        <div className="col-span-4">
          <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b">
              <h2 className="font-semibold text-lg">캠페인 목록</h2>
            </div>
            <div className="divide-y max-h-[calc(100vh-250px)] overflow-y-auto">
              {loading ? (
                <p className="p-4 text-gray-500 text-center">로딩 중...</p>
              ) : campaigns.length === 0 ? (
                <p className="p-4 text-gray-500 text-center">
                  아직 생성된 드립 캠페인이 없습니다
                </p>
              ) : (
                campaigns.map((campaign) => (
                  <div
                    key={campaign.id}
                    onClick={() => {
                      setSelectedCampaign(campaign);
                      loadCampaign(campaign.id);
                    }}
                    className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors ${
                      selectedCampaign?.id === campaign.id ? 'bg-blue-50' : ''
                    }`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-semibold">{campaign.name}</h3>
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-semibold ${getStatusBadge(
                          campaign.status
                        )}`}
                      >
                        {campaign.status.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">
                      {campaign.description || '설명 없음'}
                    </p>
                    <div className="grid grid-cols-2 gap-2 text-xs text-gray-500">
                      <div>📝 {campaign.total_steps} 스텝</div>
                      <div>👥 {campaign.total_subscribers} 구독자</div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Campaign Detail & Step Builder */}
        <div className="col-span-8">
          {!selectedCampaign ? (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <p className="text-gray-500">캠페인을 선택하거나 새로 만들어보세요</p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Campaign Header */}
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h2 className="text-2xl font-bold mb-2">{selectedCampaign.name}</h2>
                    <p className="text-gray-600">{selectedCampaign.description}</p>
                    {selectedCampaign.goal && (
                      <p className="text-sm text-blue-600 mt-2">
                        🎯 목표: {selectedCampaign.goal}
                      </p>
                    )}
                  </div>
                  <div className="flex gap-2">
                    {selectedCampaign.status === 'draft' && (
                      <button
                        onClick={handleActivateCampaign}
                        className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
                      >
                        활성화
                      </button>
                    )}
                    {selectedCampaign.status === 'active' && (
                      <button
                        onClick={handlePauseCampaign}
                        className="bg-yellow-600 text-white px-4 py-2 rounded-lg hover:bg-yellow-700"
                      >
                        일시정지
                      </button>
                    )}
                    {selectedCampaign.status === 'paused' && (
                      <button
                        onClick={handleActivateCampaign}
                        className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
                      >
                        재개
                      </button>
                    )}
                  </div>
                </div>

                {/* Campaign Stats */}
                <div className="grid grid-cols-4 gap-4 mt-4 pt-4 border-t">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {selectedCampaign.active_subscribers}
                    </div>
                    <div className="text-xs text-gray-500">활성 구독자</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {selectedCampaign.total_sent}
                    </div>
                    <div className="text-xs text-gray-500">총 발송</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {selectedCampaign.total_opens}
                    </div>
                    <div className="text-xs text-gray-500">총 오픈</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">
                      {selectedCampaign.completed_subscribers}
                    </div>
                    <div className="text-xs text-gray-500">완료</div>
                  </div>
                </div>
              </div>

              {/* Steps */}
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-xl font-semibold">캠페인 스텝</h3>
                  <button
                    onClick={() => {
                      setEditingStep(null);
                      resetStepForm();
                      setShowStepModal(true);
                    }}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm"
                  >
                    + 스텝 추가
                  </button>
                </div>

                {selectedCampaign.steps.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">
                    아직 스텝이 없습니다. 첫 스텝을 추가해보세요!
                  </p>
                ) : (
                  <div className="space-y-4">
                    {selectedCampaign.steps.map((step, index) => (
                      <div
                        key={step.id}
                        className="border-l-4 border-blue-500 bg-gray-50 p-4 rounded-r-lg relative"
                      >
                        {/* Step Number */}
                        <div className="absolute -left-6 top-4 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
                          {step.step_order}
                        </div>

                        {/* Delay Badge */}
                        {index > 0 && (
                          <div className="absolute -top-3 left-8 bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-xs font-semibold">
                            ⏱ {getTotalDelay(step)} 후
                          </div>
                        )}

                        <div className="pl-4">
                          <div className="flex justify-between items-start mb-2">
                            <div>
                              <h4 className="font-semibold text-lg">{step.name}</h4>
                              <div className="flex gap-2 mt-1">
                                <span className="px-2 py-1 bg-purple-200 text-purple-800 rounded text-xs font-semibold">
                                  {step.message_type.toUpperCase()}
                                </span>
                                <span className="px-2 py-1 bg-gray-200 text-gray-800 rounded text-xs">
                                  {step.condition_type}
                                </span>
                              </div>
                            </div>
                            <div className="flex gap-2">
                              <button
                                onClick={() => openEditStep(step)}
                                className="text-blue-600 hover:text-blue-800 text-sm"
                              >
                                수정
                              </button>
                              <button
                                onClick={() => handleDeleteStep(step.id)}
                                className="text-red-600 hover:text-red-800 text-sm"
                              >
                                삭제
                              </button>
                            </div>
                          </div>

                          {step.subject && (
                            <p className="text-sm text-gray-700 mb-1">
                              <strong>제목:</strong> {step.subject}
                            </p>
                          )}

                          <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                            {step.content}
                          </p>

                          {step.cta_text && (
                            <p className="text-sm text-blue-600">
                              🔗 CTA: {step.cta_text}
                            </p>
                          )}

                          {/* Step Stats */}
                          <div className="grid grid-cols-4 gap-2 mt-3 pt-3 border-t text-xs">
                            <div className="text-center">
                              <div className="font-bold">{step.sent_count}</div>
                              <div className="text-gray-500">발송</div>
                            </div>
                            <div className="text-center">
                              <div className="font-bold">{step.delivered_count}</div>
                              <div className="text-gray-500">전달</div>
                            </div>
                            <div className="text-center">
                              <div className="font-bold">{step.opened_count}</div>
                              <div className="text-gray-500">오픈</div>
                            </div>
                            <div className="text-center">
                              <div className="font-bold">{step.clicked_count}</div>
                              <div className="text-gray-500">클릭</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Create Campaign Modal */}
      {showCampaignModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold">새 드립 캠페인 생성</h2>
                <button
                  onClick={() => {
                    setShowCampaignModal(false);
                    resetCampaignForm();
                  }}
                  className="text-gray-500 hover:text-gray-700 text-2xl"
                >
                  ×
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    캠페인 이름 *
                  </label>
                  <input
                    type="text"
                    value={campaignForm.name}
                    onChange={(e) =>
                      setCampaignForm({ ...campaignForm, name: e.target.value })
                    }
                    className="w-full border border-gray-300 rounded-lg px-4 py-2"
                    placeholder="예: 신규 고객 온보딩"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    설명
                  </label>
                  <textarea
                    value={campaignForm.description}
                    onChange={(e) =>
                      setCampaignForm({ ...campaignForm, description: e.target.value })
                    }
                    className="w-full border border-gray-300 rounded-lg px-4 py-2"
                    rows={3}
                    placeholder="캠페인에 대한 간단한 설명"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    목표
                  </label>
                  <input
                    type="text"
                    value={campaignForm.goal}
                    onChange={(e) =>
                      setCampaignForm({ ...campaignForm, goal: e.target.value })
                    }
                    className="w-full border border-gray-300 rounded-lg px-4 py-2"
                    placeholder="예: 신규 사용자의 첫 구매 유도"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    트리거 유형
                  </label>
                  <select
                    value={campaignForm.trigger_type}
                    onChange={(e) =>
                      setCampaignForm({ ...campaignForm, trigger_type: e.target.value })
                    }
                    className="w-full border border-gray-300 rounded-lg px-4 py-2"
                  >
                    <option value="manual">수동 추가</option>
                    <option value="signup">회원 가입 시</option>
                    <option value="purchase">구매 시</option>
                    <option value="lead_created">리드 생성 시</option>
                  </select>
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <button
                    onClick={() => {
                      setShowCampaignModal(false);
                      resetCampaignForm();
                    }}
                    className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    취소
                  </button>
                  <button
                    onClick={handleCreateCampaign}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    생성
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add/Edit Step Modal */}
      {showStepModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold">
                  {editingStep ? '스텝 수정' : '새 스텝 추가'}
                </h2>
                <button
                  onClick={() => {
                    setShowStepModal(false);
                    resetStepForm();
                    setEditingStep(null);
                  }}
                  className="text-gray-500 hover:text-gray-700 text-2xl"
                >
                  ×
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    스텝 이름 *
                  </label>
                  <input
                    type="text"
                    value={stepForm.name}
                    onChange={(e) => setStepForm({ ...stepForm, name: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2"
                    placeholder="예: 환영 이메일"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    메시지 유형 *
                  </label>
                  <select
                    value={stepForm.message_type}
                    onChange={(e) =>
                      setStepForm({
                        ...stepForm,
                        message_type: e.target.value as 'email' | 'sms',
                      })
                    }
                    className="w-full border border-gray-300 rounded-lg px-4 py-2"
                  >
                    <option value="email">이메일</option>
                    <option value="sms">SMS</option>
                  </select>
                </div>

                {/* Delay Settings */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    대기 시간 (이전 스텝 후)
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <input
                        type="number"
                        min="0"
                        value={stepForm.delay_days}
                        onChange={(e) =>
                          setStepForm({
                            ...stepForm,
                            delay_days: Number(e.target.value),
                          })
                        }
                        className="w-full border border-gray-300 rounded-lg px-4 py-2"
                        placeholder="일"
                      />
                      <span className="text-xs text-gray-500">일</span>
                    </div>
                    <div>
                      <input
                        type="number"
                        min="0"
                        max="23"
                        value={stepForm.delay_hours}
                        onChange={(e) =>
                          setStepForm({
                            ...stepForm,
                            delay_hours: Number(e.target.value),
                          })
                        }
                        className="w-full border border-gray-300 rounded-lg px-4 py-2"
                        placeholder="시간"
                      />
                      <span className="text-xs text-gray-500">시간</span>
                    </div>
                    <div>
                      <input
                        type="number"
                        min="0"
                        max="59"
                        value={stepForm.delay_minutes}
                        onChange={(e) =>
                          setStepForm({
                            ...stepForm,
                            delay_minutes: Number(e.target.value),
                          })
                        }
                        className="w-full border border-gray-300 rounded-lg px-4 py-2"
                        placeholder="분"
                      />
                      <span className="text-xs text-gray-500">분</span>
                    </div>
                  </div>
                </div>

                {stepForm.message_type === 'email' && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        이메일 제목
                      </label>
                      <input
                        type="text"
                        value={stepForm.subject}
                        onChange={(e) =>
                          setStepForm({ ...stepForm, subject: e.target.value })
                        }
                        className="w-full border border-gray-300 rounded-lg px-4 py-2"
                        placeholder="이메일 제목"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        발신자 이름
                      </label>
                      <input
                        type="text"
                        value={stepForm.from_name}
                        onChange={(e) =>
                          setStepForm({ ...stepForm, from_name: e.target.value })
                        }
                        className="w-full border border-gray-300 rounded-lg px-4 py-2"
                        placeholder="발신자 이름"
                      />
                    </div>
                  </>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    메시지 내용 *
                  </label>
                  <textarea
                    value={stepForm.content}
                    onChange={(e) => setStepForm({ ...stepForm, content: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2"
                    rows={6}
                    placeholder="메시지 내용을 입력하세요"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      CTA 버튼 텍스트
                    </label>
                    <input
                      type="text"
                      value={stepForm.cta_text}
                      onChange={(e) =>
                        setStepForm({ ...stepForm, cta_text: e.target.value })
                      }
                      className="w-full border border-gray-300 rounded-lg px-4 py-2"
                      placeholder="예: 시작하기"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      CTA URL
                    </label>
                    <input
                      type="text"
                      value={stepForm.cta_url}
                      onChange={(e) =>
                        setStepForm({ ...stepForm, cta_url: e.target.value })
                      }
                      className="w-full border border-gray-300 rounded-lg px-4 py-2"
                      placeholder="https://..."
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    발송 조건
                  </label>
                  <select
                    value={stepForm.condition_type}
                    onChange={(e) =>
                      setStepForm({ ...stepForm, condition_type: e.target.value })
                    }
                    className="w-full border border-gray-300 rounded-lg px-4 py-2"
                  >
                    <option value="always">항상 발송</option>
                    <option value="opened_previous">이전 메시지 오픈함</option>
                    <option value="clicked_previous">이전 메시지 클릭함</option>
                    <option value="not_opened_previous">이전 메시지 오픈 안함</option>
                    <option value="not_clicked_previous">이전 메시지 클릭 안함</option>
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    첫 번째 스텝이 아닌 경우 조건에 따라 발송 여부가 결정됩니다
                  </p>
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <button
                    onClick={() => {
                      setShowStepModal(false);
                      resetStepForm();
                      setEditingStep(null);
                    }}
                    className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    취소
                  </button>
                  <button
                    onClick={handleAddStep}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    {editingStep ? '수정' : '추가'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
