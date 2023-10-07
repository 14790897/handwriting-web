const nodemailer = require("nodemailer");

module.exports = async (req, res) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader(
    "Access-Control-Allow-Methods",
    "GET, POST, OPTIONS, PUT, PATCH, DELETE"
  );
  res.setHeader(
    "Access-Control-Allow-Headers",
    "X-Requested-With,content-type"
  );
  // 对于预检请求，返回正常状态
  if ("OPTIONS" === req.method) {
    return res.status(200).send("OK")
  } else if (req.method === "POST") {
    // 从POST请求中获取电子邮件和反馈信息
    const { email, feedback } = req.body;

    if (!email || !feedback) {
      return res.status(400).send({ error: "Email and feedback are required" });
    }

    // 创建一个SMTP客户端配置对象
    const transporter = nodemailer.createTransport({
      service: "gmail",
      auth: {
        user: process.env.EMAIL_USER,
        pass: process.env.EMAIL_PASS,
      },
    });

    // 设置邮件内容
    const mailOptions = {
      from: process.env.EMAIL_USER,
      to: process.env.EMAIL_USER,
      subject: "New Feedback Received In Handwrite",
      text: `Email: ${email}\nFeedback: ${feedback}`,
      html: `<p><strong>Email:</strong> ${email}</p><p><strong>Feedback:</strong> ${feedback}</p>`,
    };

    // 发送邮件
    try {
      await transporter.sendMail(mailOptions);
      res.status(200).send({ message: "Email sent successfully." });
    } catch (error) {
      console.error("Error occurred while sending email:", error);
      res.status(500).send({ error: "Failed to send email." });
    }
  } else {
    res.status(405).send({ error: "Method not allowed" });
  }
};
