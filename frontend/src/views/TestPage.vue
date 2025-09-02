<template>
  <div style="padding: 20px; background: #f0f0f0; min-height: 100vh;">
    <h1 style="color: #333;">测试页面</h1>
    <p>如果你能看到这个页面，说明前端正常工作！</p>
    <div style="margin: 20px 0;">
      <h2>系统状态</h2>
      <ul>
        <li>✅ Vue.js 已加载</li>
        <li>✅ 路由系统正常</li>
        <li>✅ 组件渲染成功</li>
      </ul>
    </div>
    <button @click="testClick" style="padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
      测试点击事件
    </button>
  </div>
</template>

<script setup>
console.log('✅ TestPage component loaded')

const testClick = () => {
  alert('按钮点击正常！前端功能运行正常。')
  console.log('✅ Button clicked successfully')
}
</script>