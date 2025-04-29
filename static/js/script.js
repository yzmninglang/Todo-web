
// 只对带有 confirm-delete 类的按钮进行处理
document.querySelectorAll('.confirm-delete').forEach(button => {
    button.addEventListener('click', function(event) {
        // 阻止默认提交行为
        event.preventDefault();

        // 弹出确认框
        const isConfirmed = confirm("确定要删除这个任务吗？");

        // 如果用户确认了，就提交它所在的表单
        if (isConfirmed) {
            this.closest('form').submit(); // 找到最近的 <form> 并提交
        }
    });
});