import { Select } from 'antd';

const POPULAR_MODELS = [
  { label: 'GPT-4o', value: 'gpt-4o' },
  { label: 'GPT-4o Mini', value: 'gpt-4o-mini' },
  { label: 'GPT-5', value: 'gpt-5' },
  { label: 'Claude 3.5 Sonnet', value: 'claude-3-5-sonnet-20241022' },
  { label: 'Claude 4 Opus', value: 'claude-4-opus' },
  { label: '通义千问 Max', value: 'qwen-max' },
  { label: '通义千问 Plus', value: 'qwen-plus' },
  { label: '通义千问 Turbo', value: 'qwen-turbo' },
  { label: 'DeepSeek V3', value: 'deepseek-chat' },
  { label: 'DeepSeek R1', value: 'deepseek-reasoner' },
  { label: 'Gemini 2.0 Flash', value: 'gemini-2.0-flash' },
  { label: 'Gemini 2.0 Pro', value: 'gemini-2.0-pro-exp' },
];

export default function ModelSelector(props) {
  return (
    <Select
      showSearch
      placeholder="选择大模型"
      options={POPULAR_MODELS}
      optionFilterProp="label"
      {...props}
    />
  );
}
