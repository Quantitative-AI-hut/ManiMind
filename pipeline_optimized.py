"""
黎曼猜想科普视频 — 优化版管线
==============================
17段 × ~53秒 = 15分钟 | TTS旁白 | BGM | SFX | 5种视觉模板 | 中文
"""
import json, os, sys, subprocess, asyncio, re, glob
from pathlib import Path
from dataclasses import dataclass

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "riemann-optimized"
SEGMENTS_DIR = OUTPUT_DIR / "segments"
AUDIO_DIR = OUTPUT_DIR / "audio"
TEMP_DIR = OUTPUT_DIR / "temp"
for d in [SEGMENTS_DIR, AUDIO_DIR, TEMP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ============================================================
# 28段完整脚本（17段入正片 + 6段备选 + 5段扩展）
# 结构：钩子(2) → 溯源(3) → 猜想本体(4) → 素数联系(3) → 证明之路(3) → 开放式结尾(2)
# 旁白已做口语化改写，带情绪标记
# ============================================================

NARRATION_SEGMENTS = [
    # ─── 钩子：制造悬念 ───
    {"id":"seg-01","chapter":"钩子","title":"千禧年大奖难题","selected":True,
     "narration":"想象一下：有一个问题，世界上最聪明的头脑花了一百六十多年都解不出来。有人悬赏一百万美元，就为了找到答案。这个问题不是关于外星人，不是关于时间旅行——它只是关于一个简单的数字规律：质数。2、3、5、7、11…… 看起来随机，对吧？但黎曼却说不是。他在1859年写下了短短八页纸，提出了一个改变数学史的猜测。今天，我们来讲这个故事。",
     "visual":"dark","duration":55},
    {"id":"seg-02","chapter":"钩子","title":"质数的召唤","selected":True,
     "narration":"先做个小实验。你面前有从一到一百的所有整数。请把所有质数挑出来——它们像夜晚的星星，看不见规律。现在，我们数一数：一到十里有四个质数。一到一百里有二十五个。到了一千个里面，只剩下一百六十八个。质数在变少，但变少的速度有没有公式？高斯才十五岁的时候就发现了：有。",
     "visual":"prime_spiral","duration":50},

    # ─── 溯源：从欧拉到黎曼 ───
    {"id":"seg-03","chapter":"溯源","title":"巴塞尔问题","selected":True,
     "narration":"故事要从欧拉说起。1735年，28岁的欧拉面对一个著名难题：所有整数的平方的倒数和等于多少？听起来简单？这个级数困扰了数学家近百年。欧拉给出了一个令人震惊的答案：π²除以六。它是怎么做到的？他用了一个无穷乘积，把质数和圆周率联系在了一起。这就是质数与分析学第一次深度握手。",
     "visual":"classical","duration":52},
    {"id":"seg-04","chapter":"溯源","title":"ζ函数的诞生","selected":True,
     "narration":"欧拉的天才启发了黎曼。黎曼把问题倒过来：我不是要算质数——我要研究一个函数，让这个函数自己把质数的秘密吐出来。于是他定义了ζ函数。s 是一个复数。把一除以一的s次方，加上一除以二的s次方，加一除以三的s次方……一直加到无穷。这听起来像是自找麻烦，对吧？但黎曼看出了别人看不到的东西。",
     "visual":"formula_build","duration":54},
    {"id":"seg-05","chapter":"溯源","title":"解析延拓的魔法","selected":True,
     "narration":"但有个问题。刚才那个无穷级数，只有在s的实部大于一的时候才收敛。小于一呢？级数发散，炸了。黎曼说：没关系，我有办法。他用了当时最高级的分析技巧——解析延拓。想象你在画一条曲线，画到一半看不见了，但你凭感觉可以平滑地继续画下去。黎曼就把ζ函数平滑地扩展到了整个复平面。除了s等于一那个点——那里有个洞，永远填不上。",
     "visual":"extension","duration":55},

    # ─── 猜想本体 ───
    {"id":"seg-06","chapter":"猜想本体","title":"零点的秘密","selected":True,
     "narration":"现在ζ函数可以在整个复平面上跳舞了。黎曼开始问：这个函数在哪里等于零？零点——函数图像碰到地面的地方。他发现了两类零点。第一类叫平凡零点，在负偶数上，很规矩。第二类叫非平凡零点——它们藏在一个带状区域里，实部在零到一之间。黎曼算出了前几个非平凡零点。猜猜它们的实部是多少？二分之一。全部是二分之一。",
     "visual":"zero_distribution","duration":54},
    {"id":"seg-07","chapter":"猜想本体","title":"临界线的预言","selected":True,
     "narration":"黎曼抬起头，写下了那个改变一切的猜想：ζ函数的所有非平凡零点，都在实部等于二分之一的这条线上。这条线，后来被称为临界线。你想象一下——复平面是一条无尽的平面，零点就像散落的珍珠。黎曼说：所有的珍珠都正好串在这一条垂直的线上。一条线，串起无穷个零点。这是一百六十年没人能证明的预言。",
     "visual":"critical_line","duration":53},
    {"id":"seg-08","chapter":"猜想本体","title":"为什么是½？","selected":True,
     "narration":"你可能会问：为什么偏偏是二分之一？不是零点三、不是零点七？答案藏在函数方程的对称性里。黎曼发现ζ函数有一个漂亮的对称关系：把s换成一减s，函数值有一个确定的比例关系。这就好比你照镜子——左边和右边虽然不一样，但可以通过一个公式换算。而唯一在镜子里不变的，就是中点：二分之一。对称性，把零点钉在了临界线上。",
     "visual":"symmetry","duration":56},
    {"id":"seg-09","chapter":"猜想本体","title":"前一百亿个零点","selected":True,
     "narration":"到目前为止，数学家们用超级计算机算出了超过十万亿个非平凡零点。每一个，实部都恰好是二分之一。没有一个例外。十万亿个证据，够不够？在数学里，不够。因为你没办法证明第一十万亿零一个也遵守这个规律。这就是数学的残酷与美丽——你可以在实验里验证一辈子，但你必须用纯粹的推理来证明它永远成立。",
     "visual":"zero_wave","duration":55},

    # ─── 素数联系 ───
    {"id":"seg-10","chapter":"素数联系","title":"显式公式","selected":True,
     "narration":"现在最有意思的部分来了。黎曼为什么要费这么大劲研究零点？因为零点直接控制着质数的分布。黎曼推导出了一个叫做显式公式的东西——他说，质数计数函数的误差，恰好等于对所有零点的某种求和。每一个非平凡零点，都像质数世界里的一个音符。零点越靠近临界线，质数就越有规律。如果所有零点都在临界线上——那质数的分布就可以精确到你想精确的任何程度。",
     "visual":"prime_zero_link","duration":57},
    {"id":"seg-11","chapter":"素数联系","title":"素数定理的精确版","selected":True,
     "narration":"1896年，哈达玛和普桑独立证明了素数定理——质数密度约等于一除以自然对数。这已经够惊人的了。但如果黎曼猜想成立，我们可以得到更好的结果：误差项可以从x的任意次方压到x的平方根乘以对数。差距是天文数字。你电脑上的RSA加密，背后依赖的就是质数——黎曼猜想的真假，直接关系到现代密码学的安全性。",
     "visual":"data_overlay","duration":55},
    {"id":"seg-12","chapter":"素数联系","title":"量子共鸣","selected":True,
     "narration":"更妙的是，1972年，物理学家发现了一件神奇的事。在量子混沌系统中，能级之间的间距分布，和黎曼ζ函数零点之间的间距分布——惊人地相似。一个纯数学的猜想，居然和物理世界的量子行为共享同一套统计规律。这意味着什么？也许黎曼猜想的证明藏在某个量子系统里。也许质数不是随机的——它们是某种未知物理法则的指纹。",
     "visual":"quantum_parallel","duration":56},

    # ─── 证明之路 ───
    {"id":"seg-13","chapter":"证明之路","title":"哈代的突破","selected":True,
     "narration":"1914年，英国数学家哈代取得了第一个重大突破。他证明了：ζ函数有无穷多个零点恰好落在临界线上。不是全部——但有无穷多个。这是一小步，但至少证明了黎曼没说错——临界线上确实有无穷无尽的零点。哈代的证明用了一个巧妙的分析技巧，他后来写道：我证明了无穷多个零点在线上，但没保证其他零点不在线外。这是典型的数学家幽默。",
     "visual":"classical","duration":54},
    {"id":"seg-14","chapter":"证明之路","title":"百分比战争","selected":True,
     "narration":"哈代之后，数学家们开始了一场无声的竞赛：临界线上零点占比能提高到多少？塞尔伯格在1942年证明：至少有一定比例的零点在线上了。莱文森在1974年把这个比例推到了至少三分之一。而康瑞在1989年证明：至少五分之二的零点在临界线上。到了今天，我们知道至少百分之四十一的非平凡零点都在临界线上。但黎曼要的不是百分之四十一——他要的是百分之百。",
     "visual":"progress","duration":56},
    {"id":"seg-15","chapter":"证明之路","title":"阿蒂亚的尝试","selected":True,
     "narration":"2018年，数学界发生了一场轰动。89岁的菲尔兹奖得主阿蒂亚宣布他证明了黎曼猜想。全世界的数学家都屏住了呼吸。他在海德堡的演讲持续了四十五分钟，幻灯片上写满了关于精细结构常数的公式。但结果令人失望——同行评审发现他的论证中存在无法弥补的漏洞。黎曼猜想，依然屹立不倒。这也许是它最气人的地方：看起来简单，却比任何人的聪明都更持久。",
     "visual":"dark","duration":58},

    # ─── 结尾 ───
    {"id":"seg-16","chapter":"结尾","title":"为什么它这么难？","selected":True,
     "narration":"那么问题来了：为什么黎曼猜想到底这么难？因为它不是在一个维度上运作的。它牵扯复分析、数论、调和分析、代数几何，甚至量子物理。你试图证明所有零点在一条线上——但你面对的是一个无穷维的函数空间。每一个零点都是一个方程，无穷个零点意味着无穷个方程需要同时满足。这就像你同时在解无穷个拼图，而每块拼图都和所有其他拼图互相影响。",
     "visual":"complexity","duration":57},
    {"id":"seg-17","chapter":"结尾","title":"留给你","selected":True,
     "narration":"回到开头那个问题。一百六十多年过去了，一百万美元还在那儿。也许读到这里的你，有一天会找到那把钥匙。也许不是靠更快的计算机——因为计算机已经验证了十万亿个零点，问题不在这儿。黎曼猜想的证明需要的是一种全新的看待问题的方式。就像黎曼本人当年看待质数那样——不是沿着数轴扫过去，而是跳到复平面，从上方俯视。如果你有朝一日做到了，记得回来告诉我答案。我等你。",
     "visual":"ending","duration":60},

    # ─── 备选段（18-23，用于替换或补充）───
    {"id":"seg-18","chapter":"备选","title":"欧拉乘积公式","selected":False,
     "narration":"我们再仔细看看欧拉的天才。他发现ζ函数可以写成所有质数因子的无穷连乘。左边是所有整数的求和，右边是所有质数的连乘。相等的。这意味着质数不是孤立的——它们通过一种深刻的乘法结构，编码在每一个整数的倒数和里。这简直像一句咒语：把质数的魔力从自然数中召唤出来。欧拉没有意识到，他刚刚打开了通往黎曼猜想的第一扇门。",
     "visual":"classical","duration":52},
    {"id":"seg-19","chapter":"备选","title":"复平面可视化入门","selected":False,
     "narration":"在继续之前，让我们快速熟悉一下复平面。横轴是实部，纵轴是虚部。普通的实数只在横轴上移动——一条线。但复数可以在这整个平面上跳舞。ζ函数吃进一个复平面上的点，吐出一个复数。你没法在纸上画出四维的图像——输入两维、输出两维——但你可以画颜色：用颜色的深浅表示输出的大小，用色相表示输出的角度。这就是我们接下来看到的那些绚丽图像的原理。",
     "visual":"complex_plane_intro","duration":54},
    {"id":"seg-20","chapter":"备选","title":"黎曼-西格尔公式","selected":False,
     "narration":"计算第十万亿个零点的实部是不是二分之一——你不可能用定义式去算，级数收敛太慢了。1932年，西格尔在黎曼未发表的手稿中发现了一个公式，可以在临界线上高效计算ζ函数的值。这就是黎曼-西格尔公式。它把ζ函数展开成一系列振荡项的和。用这个公式，现代计算机可以在几秒钟内验证一个零点的位置。如果黎曼没有写下这个公式，我们可能至今只能验证前几十个零点。",
     "visual":"formula_build","duration":55},
    {"id":"seg-21","chapter":"备选","title":"蒙哥马利对关联猜想","selected":False,
     "narration":"1972年，普林斯顿的茶歇时间。数学家蒙哥马利刚做完了博士论文，内容是关于黎曼零点之间的间距分布。他去和戴森喝茶——戴森是物理学家，研究原子核的能级。蒙哥马利描述了他的统计结果。戴森惊呆了：这和随机矩阵的特征值分布一模一样。一个纯数论的零点，和一个量子核的能级，遵循同一个统计规律。这次茶歇，诞生了数学和物理之间最深刻的一次对话。",
     "visual":"data_overlay","duration":58},
    {"id":"seg-22","chapter":"备选","title":"广义黎曼猜想","selected":False,
     "narration":"黎曼猜想的阴影下还有更可怕的版本。有一类函数叫L函数——它们和ζ函数长得很像，但带着额外的参数。广义黎曼猜想断言：所有这些L函数的非平凡零点，也都落在临界线上。如果广义黎曼猜想成立，成千上万个数论定理会瞬间得证——因为很多定理都说：在广义黎曼猜想成立的假设下，我们有如下结论……所有写这种话的论文都在赌一件事：有人会证明它。但至今没人做到。",
     "visual":"extension","duration":56},
    {"id":"seg-23","chapter":"备选","title":"梅尔滕斯猜想陨落","selected":False,
     "narration":"这是一个警示故事。有个猜想叫梅尔滕斯猜想，它比黎曼猜想弱得多。如果梅尔滕斯猜想成立，黎曼猜想自动成立。1985年，数学家们用计算机找到了反例——梅尔滕斯猜想是错误的。但黎曼猜想呢？它依然是对的，至少十万亿个零点都支持它。这个故事告诉我们：你找不到反例，并不代表你能证明它。但至少——黎曼猜想比梅尔滕斯猜想顽强得多。",
     "visual":"dark","duration":53},

    # ─── 扩展段（24-28，超出15分钟时的额外内容）───
    {"id":"seg-24","chapter":"扩展","title":"一千美元与一百万美元","selected":False,
     "narration":"其实有两个悬赏。1900年，希尔伯特把黎曼猜想列入他的二十三个问题之一——这些问题为二十世纪的数学画了地图。2000年，克雷数学研究所又把它列为七个千禧年大奖难题之一，悬赏一百万美元。但1908年，有个德国数学家叫沃尔夫斯凯尔，因为感情受挫想在半夜自杀。他为了分散注意力读了一篇关于黎曼猜想的论文，读着读着忘记了自杀。天亮后，他把遗产设为一个奖项：谁证明黎曼猜想，奖十万马克。数学真的可以救人一命。",
     "visual":"classical","duration":57},
    {"id":"seg-25","chapter":"扩展","title":"黎曼的手稿","selected":False,
     "narration":"黎曼1859年的原始论文只有八页。八页纸，改变了整个数学史。有趣的是，黎曼并没有把这当成他最重要的贡献——他似乎是顺手为之。他的管家在他去世后烧掉了大量未发表的手稿，理由是那些纸太乱了。我们永远不知道那些灰烬里是不是藏着黎曼猜想的证明。黎曼四十一岁死于肺结核。一个天才，一个问题，一撮灰烬，和一个至今没有答案的谜。",
     "visual":"dark","duration":56},
    {"id":"seg-26","chapter":"扩展","title":"素数在三维","selected":False,
     "narration":"有没有办法把质数画出来？有一个经典的方法叫乌拉姆螺旋。把整数按螺旋排列，然后把质数涂黑——你会看到惊人的对角线条纹。这些纹路至今没有完全解释清楚。它们暗示质数有一种更深的几何结构，藏在数轴的直线排列下面。也许有一天，我们会发现，质数是用我们还没发明的几何学书写的密码。",
     "visual":"prime_spiral","duration":52},
    {"id":"seg-27","chapter":"扩展","title":"Δ 函数与模形式","selected":False,
     "narration":"证明黎曼猜想的主流方案之一是模形式路径。模形式是一种高度对称的复变函数，它们的傅里叶系数和质数分布有神秘的联系。拉马努金就是研究模形式的天才。他凭直觉写下了无数关于模形式系数的猜想，几乎全部事后被证明正确。如果能把ζ函数和某种模形式之间的桥梁完全架通——黎曼猜想也许就能降落在那里。这条路径虽然走了一百多年还没走完，但每一步都让数学的版图扩大一圈。",
     "visual":"symmetry","duration":57},
    {"id":"seg-28","chapter":"扩展","title":"临界线全息图","selected":False,
     "narration":"最后一个想法，有点疯狂。有人猜测，所有的非平凡零点构成了一种编码——就像一张全息图，包含了所有质数的信息。在物理里，全息原理说三维空间的信息可以编码在二维平面上。对于质数：无穷维的质数分布，被编码在一维的临界线上。二维平面上的零点，还原出整个质数世界。如果有一天我们破解了这个编码——我们能做的事情，可能远远超出密码学。我们可能会读通宇宙的源代码。",
     "visual":"ending","duration":60},
]

# ============================================================
# 视觉模板定义
# ============================================================

VISUAL_TEMPLATES = {
    "dark": {
        "bg_color": "#0A0A1A", "title_color": "#FFD700",
        "accent": "#FF3333", "secondary": "#8888FF",
        "description": "暗蓝神秘风 — 开场悬念 / 庄重段落"
    },
    "classical": {
        "bg_color": "#1A1520", "title_color": "#E8C97A",
        "accent": "#C49B4A", "secondary": "#7B9CB5",
        "description": "暖金古典风 — 历史溯源 / 人物故事"
    },
    "prime_spiral": {
        "bg_color": "#0D1117", "title_color": "#58A6FF",
        "accent": "#3FB950", "secondary": "#F78166",
        "description": "科技冷色风 — 质数可视化 / 数据展示"
    },
    "formula_build": {
        "bg_color": "#0F0F1A", "title_color": "#E0E0FF",
        "accent": "#6CB4FF", "secondary": "#FFB74D",
        "description": "纯净公式风 — 公式推导 / 步骤展示"
    },
    "data_overlay": {
        "bg_color": "#0A0F0A", "title_color": "#7DE87D",
        "accent": "#4CAF50", "secondary": "#FFD54F",
        "description": "数据科技风 — 图表叠加 / 对比展示"
    },
    "extension": {
        "bg_color": "#1A0A2E", "title_color": "#D4A5FF",
        "accent": "#B388FF", "secondary": "#69F0AE",
        "description": "深邃紫韵风 —  抽象概念 / 延拓展示"
    },
    "symmetry": {
        "bg_color": "#12121A", "title_color": "#FFFFFF",
        "accent": "#FF6F00", "secondary": "#42A5F5",
        "description": "对称极简风 — 对称性 / 方程展示"
    },
    "zero_distribution": {
        "bg_color": "#000510", "title_color": "#00E5FF",
        "accent": "#FF1744", "secondary": "#76FF03",
        "description": "深空零点风 — 零点分布 / 临界线"
    },
}

def get_selected_segments():
    return [s for s in NARRATION_SEGMENTS if s["selected"]]

def get_chapter_intro(chapter_name):
    mapping = {
        "钩子": "你知道吗，有一个数学问题悬赏了一百万美元，一百六十年没人能解。",
        "溯源": "要理解这个猜想，我们得从它的源头说起。",
        "猜想本体": "现在，让我们直面黎曼猜想本身。",
        "素数联系": "研究零点不是为了零点本身——是为了揭开质数的秘密。",
        "证明之路": "一百六十年过去了，数学家们走到了哪里？",
        "结尾": "故事到这里，该交给你了。",
    }
    return mapping.get(chapter_name, "")

# ============================================================
# Manim 脚本生成器
# ============================================================

def generate_manim_script(seg, template_color, index):
    """为单个段生成差异化 Manim 脚本"""
    t = template_color
    sid = seg["id"]
    title = seg["title"]
    narration = seg["narration"]
    visual = seg["visual"]
    duration = seg.get("duration", 53)

    # 关键公式映射
    formula_map = {
        "dark": [r"\zeta(s) = \sum_{n=1}^{\infty} \frac{1}{n^s}"],
        "classical": [r"\sum_{n=1}^\infty \frac{1}{n^2} = \frac{\pi^2}{6}"],
        "prime_spiral": [r"\pi(x) \sim \frac{x}{\ln x}"],
        "formula_build": [r"\zeta(s)=\sum_{n=1}^{\infty}\frac{1}{n^s}", r"\Re(s)>1"],
        "data_overlay": [r"\pi(x) = \operatorname{Li}(x) - \sum_{\rho} \operatorname{Li}(x^\rho)"],
        "extension": [r"\zeta(s)=2^s\pi^{s-1}\sin\left(\frac{\pi s}{2}\right)\Gamma(1-s)\zeta(1-s)"],
        "symmetry": [r"\xi(s)=\xi(1-s)", r"\Re(s)=\frac{1}{2}"],
        "zero_distribution": [r"\zeta\left(\frac{1}{2}+it\right)=0"],
        "critical_line": [r"\Re(s)=\frac{1}{2}"],
        "complexity": [r"\zeta(s)=0"],
        "ending": [r"\zeta(s)=0"],
        "progress": [r">41\%\text{ on critical line}"],
        "quantum_parallel": [r"P(s) \sim e^{-s}"],
        "zero_wave": [r"\zeta\left(\frac{1}{2}+it\right)=0"],
        "prime_zero_link": [r"\psi(x)=x-\sum_{\rho}\frac{x^\rho}{\rho}-\ln(2\pi)-\frac{1}{2}\ln(1-x^{-2})"],
    }
    formulas = formula_map.get(visual, [r"\zeta(s)=0"])

    # 根据索引选择动画变体（4种模式轮换，避免重复）
    anim_mode = index % 4
    anim_variants = {
        0: "fade_in_sequence",    # 逐条淡入
        1: "write_from_center",   # 从中心展开
        2: "transform_morph",     # 变换动画
        3: "particle_flow",       # 粒子流动
    }
    mode = anim_variants[anim_mode]

    # 根据章节决定是否加入数据可视化元素
    chapter = seg["chapter"]
    has_data_viz = chapter in ["素数联系", "证明之路"]
    has_particle_bg = visual in ["dark", "zero_distribution", "ending"]
    has_symbol_journey = visual in ["extension", "symmetry"]
    has_grid = visual in ["prime_spiral", "data_overlay", "zero_distribution"]
    has_zeta_symbol = True  # 每段都有的ζ符号装饰

    script = f'''"""
{seg["id"]}: {title} — Manim 动画脚本
模板: {visual} | 动画模式: {mode} | 时长目标: {duration}s
"""
from manim import *
import numpy as np
import random

class {sid.replace("-","_").title()}(Scene):
    def construct(self):
        # 背景
        bg = Rectangle(width=config.frame_width, height=config.frame_height,
                       fill_color="{t['bg_color']}", fill_opacity=1, stroke_width=0)
        self.add(bg)

        # 顶部标题
        title = Text("{title}", font_size=38, color="{t['title_color']}", font="Microsoft YaHei")
        title.to_edge(UP, buff=0.6)
        self.play(Write(title), run_time=1.2)

        # ζ符号装饰（右上角）
        zeta_decor = MathTex(r"\\zeta", font_size=72, color="{t['accent']}", fill_opacity=0.12)
        zeta_decor.to_corner(UR, buff=0.5)
        self.add(zeta_decor)
'''

    if has_particle_bg:
        script += f'''
        # 粒子背景
        particles = VGroup(*[
            Dot(point=np.array([random.uniform(-8,8), random.uniform(-5,5), 0]),
                radius=random.uniform(0.01,0.04),
                color=random.choice(["{t['accent']}", "{t['secondary']}", "{t['title_color']}"]),
                fill_opacity=random.uniform(0.2, 0.6))
            for _ in range(80)
        ])
        self.add(particles)
'''

    if has_grid:
        script += f'''
        # 网格背景
        grid = NumberPlane(
            x_range=[-8, 8, 1], y_range=[-5, 5, 1],
            background_line_style={{"stroke_color": "{t['secondary']}", "stroke_opacity": 0.08}},
            axis_config={{"stroke_opacity": 0.15}}
        )
        self.add(grid)
'''

    script += f'''
        # 核心内容区域
        content_group = VGroup()
'''

    # 主公式
    for i, f in enumerate(formulas):
        y_pos = 0.8 - i * 1.2
        script += f'''
        formula_{i} = MathTex(r"{f}", font_size=44, color="{t['accent']}")
        formula_{i}.move_to([0, {y_pos}, 0])
'''

        if mode == "fade_in_sequence":
            script += f'''
        self.play(FadeIn(formula_{i}, shift=UP*0.3), run_time=0.8)
        self.wait(0.3)
'''
        elif mode == "write_from_center":
            script += f'''
        self.play(Write(formula_{i}), run_time=1.0)
        self.wait(0.3)
'''
        elif mode == "transform_morph":
            script += f'''
        self.play(TransformFromCopy(title, formula_{i}), run_time=1.0)
'''
        elif mode == "particle_flow":
            script += f'''
        self.play(FadeIn(formula_{i}, scale=0.5), run_time=0.9)
        particles_glow = formula_{i}.copy().set_color(WHITE).set_fill_opacity(0.3).scale(1.15)
        self.play(Flash(formula_{i}, color="{t['accent']}", line_length=0.3, flash_radius=0.3), run_time=0.5)
'''

        script += f'''
        content_group.add(formula_{i})
'''

    # 章节过渡装饰（不是第一章才显示）
    if index > 0 and chapter != get_prev_chapter(seg, index):
        prev_ch = get_prev_chapter(seg, index)
        script += f'''
        # 章节过渡
        chap_text = Text("{chapter}", font_size=28, color="{t['secondary']}", font="Microsoft YaHei")
        chap_text.to_corner(UL, buff=0.8)
        self.play(FadeIn(chap_text, shift=RIGHT*0.3), run_time=0.6)
'''

    # 底部装饰线
    script += f'''
        # 底部装饰线
        line = Line(start=[-6, -3.2, 0], end=[6, -3.2, 0],
                    color="{t['secondary']}", stroke_opacity=0.2, stroke_width=1)
        self.add(line)
'''

    # 动画模式专属结尾
    if has_symbol_journey:
        script += f'''
        # ζ符号漫游
        journey_dot = Dot(color="{t['accent']}", radius=0.06)
        path = ArcBetweenPoints([-4,-1,0], [4,-1,0], angle=PI/3, color="{t['secondary']}", stroke_opacity=0.4)
        self.add(path)
        self.play(MoveAlongPath(journey_dot, path), run_time=3)
'''

    if has_data_viz:
        script += f'''
        # 数据脉冲
        for _ in range(3):
            pulse = Circle(radius=0.3, color="{t['accent']}", stroke_opacity=0.6)
            pulse.move_to([0, -1, 0])
            self.play(pulse.animate.scale(2).set_stroke(opacity=0), run_time=1.5)
            self.remove(pulse)
'''

    # 统一结尾 —— 所有元素淡出
    script += f'''
        # 段落结尾：所有元素渐变淡出
        self.wait({max(duration - 15, 3)})
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.5)
'''

    return script


def get_prev_chapter(seg, index):
    """获取上一个不同章节的名称"""
    for i in range(index - 1, -1, -1):
        if NARRATION_SEGMENTS[i]["chapter"] != seg["chapter"]:
            return NARRATION_SEGMENTS[i]["chapter"]
    return ""

# ============================================================
# TTS 生成
# ============================================================

async def generate_tts(text, output_path, voice="zh-CN-XiaoxiaoNeural"):
    """使用 edge-tts 生成语音"""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def generate_all_tts(segments):
    """为所有选定段生成 TTS 音频"""
    async def run():
        for seg in segments:
            mp3_path = AUDIO_DIR / f"{seg['id']}.mp3"
            if mp3_path.exists():
                print(f"  [跳过] {seg['id']} 音频已存在")
                continue
            print(f"  [TTS] {seg['id']}: {seg['title']}")
            await generate_tts(seg["narration"], str(mp3_path))
    asyncio.run(run())

# ============================================================
# BGM 生成（简易环境音乐合成）
# ============================================================

def generate_bgm(output_path, duration_seconds=900, mood="ambient"):
    """用 numpy 合成背景氛围音乐"""
    import numpy as np
    from pydub import AudioSegment

    sample_rate = 44100
    total_samples = int(sample_rate * duration_seconds)
    t = np.linspace(0, duration_seconds, total_samples, False)

    # 多层叠加：低音垫底 + 和弦层 + 闪烁高音
    if mood == "ambient":
        # 深沉的低音垫
        bass = 0.3 * np.sin(2 * np.pi * 55 * t) * np.exp(-0.0001 * t)
        bass += 0.2 * np.sin(2 * np.pi * 65.4 * t)
        # 温暖的和弦层
        pad = 0.15 * np.sin(2 * np.pi * 220 * t) * (0.5 + 0.5 * np.sin(0.5 * t))
        pad += 0.12 * np.sin(2 * np.pi * 277.18 * t) * (0.5 + 0.5 * np.sin(0.7 * t))
        pad += 0.1 * np.sin(2 * np.pi * 329.63 * t) * (0.5 + 0.5 * np.sin(0.9 * t))
        # 闪烁高音（星星感）
        twinkle = 0.05 * np.sin(2 * np.pi * 880 * t) * np.sin(0.3 * t) * np.sin(0.7 * t)
    elif mood == "uptempo":
        bass = 0.35 * np.sin(2 * np.pi * 82.4 * t) * np.exp(-0.00008 * t)
        pad = 0.2 * np.sin(2 * np.pi * 330 * t) * (0.5 + 0.5 * np.cos(0.4 * t))
        pad += 0.15 * np.sin(2 * np.pi * 392 * t) * (0.5 + 0.5 * np.cos(0.6 * t))
        twinkle = 0.08 * np.sin(2 * np.pi * 1200 * t) * np.sin(0.6 * t)
    else:
        bass = 0.3 * np.sin(2 * np.pi * 65.4 * t)
        pad = 0.15 * np.sin(2 * np.pi * 261.6 * t)
        twinkle = 0.05 * np.sin(2 * np.pi * 1000 * t) * np.sin(0.4 * t)

    audio = bass + pad + twinkle
    audio = audio / np.max(np.abs(audio)) * 0.7
    audio_int16 = (audio * 32767).astype(np.int16)

    seg = AudioSegment(
        audio_int16.tobytes(), frame_rate=sample_rate,
        sample_width=2, channels=1
    )
    seg.export(output_path, format="mp3", bitrate="128k")

# ============================================================
# SFX 音效生成
# ============================================================

def generate_sfx():
    """生成关键节点音效"""
    import numpy as np
    from pydub import AudioSegment
    sr = 44100

    def make_sfx(name, freq, duration, envelope, volume=0.6):
        t = np.linspace(0, duration, int(sr * duration), False)
        wave = np.sin(2 * np.pi * freq * t) * envelope(t)
        wave = wave / np.max(np.abs(wave)) * volume * 32767
        wave = wave.astype(np.int16)
        AudioSegment(wave.tobytes(), frame_rate=sr, sample_width=2, channels=1
                     ).export(str(AUDIO_DIR / f"{name}.mp3"), format="mp3")

    # 公式出现：清脆叮咚
    make_sfx("sfx_formula", 1200, 0.3, lambda t: np.exp(-8 * t))
    # 零点定位：低频共振
    make_sfx("sfx_zero", 80, 0.8, lambda t: np.exp(-3 * t) * (0.5+0.5*np.sin(15*t)))
    # 素数跳跃：电子脉冲
    make_sfx("sfx_prime", 400, 0.15, lambda t: np.exp(-20 * t))
    # 章节转场：升调滑音
    t_trans = np.linspace(0, 1.2, int(sr*1.2), False)
    freq_sweep = 200 + 600 * t_trans
    sweep = np.sin(2 * np.pi * freq_sweep * t_trans) * np.exp(-2 * t_trans)
    sweep = sweep / np.max(np.abs(sweep)) * 0.5 * 32767
    sweep = sweep.astype(np.int16)
    AudioSegment(sweep.tobytes(), frame_rate=sr, sample_width=2, channels=1
                 ).export(str(AUDIO_DIR / "sfx_transition.mp3"), format="mp3")
    # 结尾钟声
    t_bell = np.linspace(0, 3.0, int(sr*3.0), False)
    bell = (np.sin(2*np.pi*528*t_bell) * 0.5 + np.sin(2*np.pi*660*t_bell) * 0.3
            + np.sin(2*np.pi*792*t_bell) * 0.2) * np.exp(-1.5 * t_bell)
    bell = bell / np.max(np.abs(bell)) * 0.6 * 32767
    bell = bell.astype(np.int16)
    AudioSegment(bell.tobytes(), frame_rate=sr, sample_width=2, channels=1
                 ).export(str(AUDIO_DIR / "sfx_bell.mp3"), format="mp3")

    print("  [SFX] 5 个音效已生成")

# ============================================================
# SRT 字幕生成
# ============================================================

def generate_srt(segments):
    """为每段生成 SRT 字幕（基于旁白文本等分）"""
    for seg in segments:
        narration = seg["narration"]
        duration = seg.get("duration", 53)
        # 按句号拆分
        sentences = re.split(r'[。！？]', narration)
        sentences = [s.strip() + '。' for s in sentences if s.strip()]
        if not sentences:
            sentences = [narration]

        chunks = []
        chars_per_sec = len(narration) / duration
        buffer = ""
        t_start = 0
        for s in sentences:
            buffer += s
            if len(buffer) >= 30 or s == sentences[-1]:
                t_end = t_start + len(buffer) / chars_per_sec
                chunks.append((t_start, min(t_end, duration), buffer))
                t_start = t_end
                buffer = ""

        srt_content = ""
        for i, (start, end, text) in enumerate(chunks, 1):
            srt_content += f"{i}\n{_fmt_time(start)} --> {_fmt_time(end)}\n{text}\n\n"

        srt_path = SEGMENTS_DIR / f"{seg['id']}.srt"
        srt_path.write_text(srt_content, encoding="utf-8")

def _fmt_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

# ============================================================
# 最终合成
# ============================================================

def composite_final(segments, bgm_path, output_path):
    """用 ffmpeg 合成最终视频"""
    # 先合并所有段的视频
    concat_list = TEMP_DIR / "concat_list.txt"
    lines = []
    for seg in segments:
        mp4 = SEGMENTS_DIR / f"{seg['id']}.mp4"
        if mp4.exists():
            lines.append(f"file '{mp4.as_posix()}'\n")
    concat_list.write_text("".join(lines), encoding="utf-8")

    raw_video = TEMP_DIR / "raw_combined.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list), "-c", "copy", str(raw_video)
    ], check=True, capture_output=True)

    # 合并所有音频
    audio_list = TEMP_DIR / "audio_list.txt"
    alines = []
    for seg in segments:
        mp3 = AUDIO_DIR / f"{seg['id']}.mp3"
        if mp3.exists():
            alines.append(f"file '{mp3.as_posix()}'\n")
    audio_list.write_text("".join(alines), encoding="utf-8")

    raw_audio = TEMP_DIR / "raw_narration.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(audio_list), "-c", "copy", str(raw_audio)
    ], check=True, capture_output=True)

    # 混合 BGM + 旁白：BGM 音量降低
    mixed_audio = TEMP_DIR / "mixed_audio.mp3"
    # 获取旁白时长
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(raw_audio)
    ], capture_output=True, text=True, check=True)
    narration_dur = float(probe.stdout.strip())

    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(raw_audio),
        "-i", str(bgm_path),
        "-filter_complex",
        f"[1:a]volume=0.15,atrim=0:{narration_dur}[bgm];[0:a][bgm]amix=inputs=2:duration=first",
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(mixed_audio)
    ], check=True, capture_output=True)

    # 最终合成视频+音频
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(raw_video),
        "-i", str(mixed_audio),
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(output_path)
    ], check=True, capture_output=True)

    return output_path

# ============================================================
# 主流程
# ============================================================

def main():
    selected = get_selected_segments()
    print(f"选中 {len(selected)} 段，估算总时长: {sum(s['duration'] for s in selected)//60}分{sum(s['duration'] for s in selected)%60}秒")

    # Phase 1: 生成 Manim 脚本
    print("\n[Phase 1] 生成 Manim 动画脚本...")
    for i, seg in enumerate(selected):
        visual = seg["visual"]
        tc = VISUAL_TEMPLATES.get(visual, VISUAL_TEMPLATES["dark"])
        script = generate_manim_script(seg, tc, i)
        script_path = SEGMENTS_DIR / f"{seg['id']}.py"
        script_path.write_text(script, encoding="utf-8")
        print(f"  [{i+1}/{len(selected)}] {seg['id']}.py ({seg['title']}) — 模板:{visual}")

    # Phase 2: SRT 字幕
    print("\n[Phase 2] 生成 SRT 字幕...")
    generate_srt(selected)
    print(f"  {len(selected)} 段 SRT 已生成")

    # Phase 3: TTS 旁白
    print("\n[Phase 3] 生成 TTS 旁白...")
    generate_all_tts(selected)

    # Phase 4: BGM
    print("\n[Phase 4] 生成 BGM 背景音乐...")
    total_dur = sum(s["duration"] for s in selected) + 60
    bgm_path = AUDIO_DIR / "bgm_ambient.mp3"
    if not bgm_path.exists():
        generate_bgm(str(bgm_path), total_dur, "ambient")
        print(f"  BGM 已生成 ({total_dur}s)")
    else:
        print("  BGM 已存在，跳过")

    # Phase 5: SFX
    print("\n[Phase 5] 生成音效...")
    sfx_file = AUDIO_DIR / "sfx_transition.mp3"
    if not sfx_file.exists():
        generate_sfx()
    else:
        print("  SFX 已存在，跳过")

    # Phase 6: 渲染 Manim
    print("\n[Phase 6] 渲染 Manim 动画...")
    for i, seg in enumerate(selected):
        output_mp4 = SEGMENTS_DIR / f"{seg['id']}.mp4"
        if output_mp4.exists():
            print(f"  [{i+1}/{len(selected)}] {seg['id']} 已渲染，跳过")
            continue
        script_file = SEGMENTS_DIR / f"{seg['id']}.py"
        scene_class = seg['id'].replace("-", "_").title()
        print(f"  [{i+1}/{len(selected)}] 渲染 {seg['id']} ({seg['title']})...")
        subprocess.run([
            "manim", "-pql", "--format", "mp4",
            str(script_file), scene_class
        ], check=True, cwd=str(SEGMENTS_DIR))
        # Manim 渲染后文件在 media/videos/ 下，移动出来
        rendered = list(SEGMENTS_DIR.rglob(f"**/{scene_class}.mp4"))
        if rendered:
            import shutil
            shutil.move(str(rendered[0]), str(output_mp4))
            print(f"    渲染完成 → {output_mp4}")

    # Phase 7: 最终合成
    print("\n[Phase 7] 最终合成...")
    final_output = OUTPUT_DIR / "riemann_hypothesis_final.mp4"
    composite_final(selected, str(bgm_path), str(final_output))
    print(f"\n  最终视频: {final_output}")
    print("=" * 60)

if __name__ == "__main__":
    main()
