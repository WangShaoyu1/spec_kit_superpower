import { Button, Card, Empty, Form, Input, Modal, Select, Space, Table, Tag, message } from 'antd'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { fetchIntentDatasetDetail, saveIntentDatasetDetail } from '../../services/api'

function cloneSamples(samples) {
  return samples.map((item) => ({
    ...item,
    required_slots: [...(item.required_slots ?? [])],
    optional_slots: [...(item.optional_slots ?? [])],
    prompt_samples: [...(item.prompt_samples ?? [])],
    negative_samples: [...(item.negative_samples ?? [])],
    entities: [...(item.entities ?? [])],
  }))
}

export function IntentLibraryDatasetDetailPage({ token }) {
  const navigate = useNavigate()
  const { libraryId, datasetId } = useParams()
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [intentOpen, setIntentOpen] = useState(false)
  const [promptOpen, setPromptOpen] = useState(false)
  const [slotOpen, setSlotOpen] = useState(false)
  const [negativeOpen, setNegativeOpen] = useState(false)
  const [entityImportOpen, setEntityImportOpen] = useState(false)
  const [selectedIntentKey, setSelectedIntentKey] = useState(null)
  const [intentForm] = Form.useForm()
  const [promptForm] = Form.useForm()
  const [slotForm] = Form.useForm()
  const [negativeForm] = Form.useForm()
  const [entityForm] = Form.useForm()

  async function loadDetail() {
    setLoading(true)
    try {
      const nextDetail = await fetchIntentDatasetDetail(token, libraryId, datasetId)
      setDetail(nextDetail)
      const nextSamples = nextDetail?.samples ?? []
      if (nextSamples.length > 0) {
        setSelectedIntentKey((current) => {
          if (current && nextSamples.some((item) => item.intent_key === current)) {
            return current
          }
          return nextSamples[0].intent_key
        })
      } else {
        setSelectedIntentKey(null)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadDetail()
  }, [token, libraryId, datasetId])

  const samples = detail?.samples ?? []
  const dataset = detail?.dataset
  const selectedSampleIndex = useMemo(() => {
    if (!samples.length) {
      return -1
    }
    const index = samples.findIndex((item) => item.intent_key === selectedIntentKey)
    return index >= 0 ? index : 0
  }, [samples, selectedIntentKey])
  const selectedSample = useMemo(() => (
    selectedSampleIndex >= 0 ? samples[selectedSampleIndex] ?? null : null
  ), [samples, selectedSampleIndex])

  useEffect(() => {
    if (!intentOpen) {
      return
    }
    intentForm.setFieldsValue(
      selectedSample
        ? {
          intent_key: selectedSample.intent_key,
          display_name: selectedSample.display_name,
        }
        : {
          intent_key: '',
          display_name: '',
        },
    )
  }, [selectedSample, intentForm, intentOpen])

  useEffect(() => {
    if (!selectedSample || !slotOpen) {
      return
    }
    slotForm.setFieldsValue({
      required_slots: (selectedSample.required_slots ?? []).map((item) => item.name).join(', '),
    })
  }, [selectedSample, slotForm, slotOpen])

  async function persistSamples(nextSamples, successMessage) {
    try {
      await saveIntentDatasetDetail(token, libraryId, datasetId, { samples: nextSamples })
      await loadDetail()
      message.success(successMessage)
      return true
    } catch (error) {
      message.error(error.message || '数据保存失败')
      return false
    }
  }

  async function handleSaveIntent(values) {
    const nextSamples = cloneSamples(samples)
    if (selectedSample && selectedSampleIndex >= 0) {
      nextSamples[selectedSampleIndex] = {
        ...nextSamples[selectedSampleIndex],
        intent_key: values.intent_key,
        display_name: values.display_name,
      }
    } else {
      nextSamples.push({
        intent_key: values.intent_key,
        display_name: values.display_name,
        required_slots: [],
        optional_slots: [],
        prompt_samples: [],
        negative_samples: [],
        entities: [],
      })
    }
    const saved = await persistSamples(nextSamples, '意图配置已保存')
    if (!saved) {
      return
    }
    setSelectedIntentKey(values.intent_key)
    setIntentOpen(false)
  }

  async function handleAddPrompt(values) {
    if (!selectedSample) {
      return
    }
    const nextSamples = cloneSamples(samples)
    nextSamples[selectedSampleIndex] = {
      ...nextSamples[selectedSampleIndex],
      prompt_samples: [...(nextSamples[selectedSampleIndex].prompt_samples ?? []), values.prompt_sample],
    }
    const saved = await persistSamples(nextSamples, '问法已新增')
    if (!saved) {
      return
    }
    setPromptOpen(false)
    promptForm.resetFields()
  }

  async function handleSaveSlots(values) {
    if (!selectedSample) {
      return
    }
    const nextSamples = cloneSamples(samples)
    nextSamples[selectedSampleIndex] = {
      ...nextSamples[selectedSampleIndex],
      required_slots: values.required_slots
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean)
        .map((item) => ({ name: item })),
    }
    const saved = await persistSamples(nextSamples, '词槽配置已保存')
    if (!saved) {
      return
    }
    setSlotOpen(false)
  }

  async function handleSaveNegative(values) {
    if (!selectedSample) {
      return
    }
    const nextSamples = cloneSamples(samples)
    nextSamples[selectedSampleIndex] = {
      ...nextSamples[selectedSampleIndex],
      negative_samples: [...(nextSamples[selectedSampleIndex].negative_samples ?? []), values.negative_sample],
    }
    const saved = await persistSamples(nextSamples, '排除问已新增')
    if (!saved) {
      return
    }
    setNegativeOpen(false)
    negativeForm.resetFields()
  }

  async function handleImportEntities(values) {
    if (!selectedSample) {
      return
    }
    const entityValues = values.entity_values
      .split(/[,\n]/)
      .map((item) => item.trim())
      .filter(Boolean)
    const synonymValues = (values.synonym_values || '')
      .split(/[,\n]/)
      .map((item) => item.trim())
      .filter(Boolean)
    const nextSamples = cloneSamples(samples)
    const nextEntities = [...(nextSamples[selectedSampleIndex].entities ?? [])]
    const existingEntityIndex = nextEntities.findIndex((item) => item.entity_name === values.entity_name)
    const nextEntity = {
      entity_name: values.entity_name,
      import_mode: values.import_mode,
      values: entityValues,
      synonyms: synonymValues,
    }
    if (existingEntityIndex >= 0) {
      nextEntities[existingEntityIndex] = nextEntity
    } else {
      nextEntities.push(nextEntity)
    }
    nextSamples[selectedSampleIndex] = {
      ...nextSamples[selectedSampleIndex],
      entities: nextEntities,
    }
    const saved = await persistSamples(nextSamples, '实体已导入')
    if (!saved) {
      return
    }
    setEntityImportOpen(false)
    entityForm.resetFields()
  }

  return (
    <div className="page-stack">
      <Card className="module-card" variant="borderless" loading={loading}>
        {dataset ? (
          <div className="page-stack">
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'flex-start' }}>
              <div>
                <div className="hero-eyebrow">Dataset Detail</div>
                <h2 className="page-title">{dataset.name}</h2>
                <Space wrap>
                  <Tag color={dataset.dataset_type === 'training' ? 'blue' : 'purple'}>{dataset.dataset_type}</Tag>
                  <Tag>{dataset.sample_count} 样本</Tag>
                  <Tag>{dataset.schema_version}</Tag>
                </Space>
              </div>
              <Space wrap>
                <Button onClick={() => navigate(`/intent-library/${libraryId}/datasets`)}>返回数据集列表</Button>
                <Button onClick={() => setIntentOpen(true)}>意图配置</Button>
                <Button onClick={() => setPromptOpen(true)} disabled={!selectedSample}>新增问法</Button>
                <Button onClick={() => setNegativeOpen(true)} disabled={!selectedSample}>相似问/排除问</Button>
                <Button onClick={() => setSlotOpen(true)} disabled={!selectedSample}>词槽配置</Button>
                <Button onClick={() => setEntityImportOpen(true)} disabled={!selectedSample}>批量导入实体</Button>
              </Space>
            </div>

            <Card title="意图样本" variant="borderless">
              {samples.length > 0 ? (
                <Table
                  pagination={{ pageSize: 8 }}
                  rowKey={(record) => record.intent_key}
                  dataSource={samples}
                  onRow={(record) => ({
                    onClick: () => setSelectedIntentKey(record.intent_key),
                  })}
                  rowClassName={(record) => (record.intent_key === selectedSample?.intent_key ? 'ant-table-row-selected' : '')}
                  columns={[
                    { title: 'intent_key', dataIndex: 'intent_key' },
                    { title: '显示名称', dataIndex: 'display_name' },
                    {
                      title: '必填槽位',
                      dataIndex: 'required_slots',
                      render: (value) => (value?.length ? value.map((item) => item.name).join(' / ') : '无'),
                    },
                    {
                      title: '问法样例',
                      dataIndex: 'prompt_samples',
                      render: (value) => (value?.length ? value.join(' / ') : '无'),
                    },
                    {
                      title: '排除问',
                      dataIndex: 'negative_samples',
                      render: (value) => (value?.length ? value.join(' / ') : '无'),
                    },
                    {
                      title: '实体',
                      dataIndex: 'entities',
                      render: (value) => (value?.length
                        ? value.map((item) => {
                          const synonymText = item.synonyms?.length ? ` (同义词: ${item.synonyms.join('/')})` : ''
                          return `${item.entity_name}: ${item.values.join('/')}${synonymText}`
                        }).join(' | ')
                        : '无'),
                    },
                  ]}
                />
              ) : (
                <Empty description="当前数据集暂无样本" />
              )}
            </Card>
          </div>
        ) : null}
      </Card>

      <Modal title="意图配置 Drawer" open={intentOpen} onCancel={() => setIntentOpen(false)} onOk={() => intentForm.submit()} okText="保存意图配置">
        <Form form={intentForm} layout="vertical" onFinish={handleSaveIntent}>
          <Form.Item name="intent_key" label="Intent Key" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="display_name" label="显示名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="新增问法 Modal" open={promptOpen} onCancel={() => setPromptOpen(false)} onOk={() => promptForm.submit()} okText="保存问法">
        <Form form={promptForm} layout="vertical" onFinish={handleAddPrompt}>
          <Form.Item name="prompt_sample" label="新增问法" rules={[{ required: true }]}>
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="相似问 / 排除问 Drawer" open={negativeOpen} onCancel={() => setNegativeOpen(false)} onOk={() => negativeForm.submit()} okText="保存排除问">
        <Form form={negativeForm} layout="vertical" onFinish={handleSaveNegative}>
          <Form.Item name="negative_sample" label="排除问" rules={[{ required: true }]}>
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="自定义词槽 Drawer" open={slotOpen} onCancel={() => setSlotOpen(false)} onOk={() => slotForm.submit()} okText="保存词槽">
        <Form form={slotForm} layout="vertical" onFinish={handleSaveSlots}>
          <Form.Item name="required_slots" label="必填槽位" rules={[{ required: true }]}>
            <Input placeholder="device, temperature" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="实体批量导入 Modal"
        open={entityImportOpen}
        onCancel={() => setEntityImportOpen(false)}
        onOk={() => entityForm.submit()}
        okText="导入实体"
      >
        <Form form={entityForm} layout="vertical" onFinish={handleImportEntities}>
          <Form.Item name="entity_name" label="实体名称" rules={[{ required: true }]} initialValue="device">
            <Input />
          </Form.Item>
          <Form.Item name="import_mode" label="导入方式" initialValue="paste">
            <Select
              options={[
                { value: 'excel', label: 'Excel' },
                { value: 'text', label: '文本' },
                { value: 'paste', label: '粘贴' },
              ]}
            />
          </Form.Item>
          <Form.Item name="entity_values" label="实体值" rules={[{ required: true }]}>
            <Input.TextArea rows={4} placeholder="烤箱, 蒸箱" />
          </Form.Item>
          <Form.Item name="synonym_values" label="同义词">
            <Input.TextArea rows={3} placeholder="智能烤箱, 嵌入式烤箱" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
