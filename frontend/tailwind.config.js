/** @type {import('tailwindcss').Config} */
module.exports = {
	content: [
		"./pages/**/*.{js,ts,jsx,tsx,mdx}",
		"./components/**/*.{js,ts,jsx,tsx,mdx}",
		"./app/**/*.{js,ts,jsx,tsx,mdx}",
	],
	darkMode: ["class", "class"],
	theme: {
    	extend: {
    		colors: {
    			primary: {
    				DEFAULT: 'hsl(var(--primary))',
    				foreground: 'hsl(var(--primary-foreground))'
    			},
    			secondary: {
    				DEFAULT: 'hsl(var(--secondary))',
    				foreground: 'hsl(var(--secondary-foreground))'
    			},
    			success: '#219653',
    			warning: '#FFA70B',
    			danger: '#D34053',
    			body: '#64748B',
    			bodydark: '#AEB7C0',
    			bodydark1: '#DEE4EE',
    			bodydark2: '#8A99AF',
    			stroke: '#E2E8F0',
    			strokedark: '#2E3A47',
    			boxdark: '#24303F',
    			'shadow-default': '0px 8px 13px -3px rgba(0, 0, 0, 0.07)',
    			gray: {
    				'2': '#F7F9FC',
    				'3': '#FAFBFC'
    			},
    			graydark: '#333A48',
    			'meta-1': '#DC3545',
    			'meta-2': '#EFF2F7',
    			'meta-3': '#10B981',
    			'meta-4': '#313D4A',
    			'meta-5': '#259AE6',
    			'meta-6': '#FFBA00',
    			'meta-7': '#FF6766',
    			'meta-8': '#F0950C',
    			'meta-9': '#E5E7EB',
    			'meta-10': '#0FADCF',
    			background: 'hsl(var(--background))',
    			foreground: 'hsl(var(--foreground))',
    			card: {
    				DEFAULT: 'hsl(var(--card))',
    				foreground: 'hsl(var(--card-foreground))'
    			},
    			popover: {
    				DEFAULT: 'hsl(var(--popover))',
    				foreground: 'hsl(var(--popover-foreground))'
    			},
    			muted: {
    				DEFAULT: 'hsl(var(--muted))',
    				foreground: 'hsl(var(--muted-foreground))'
    			},
    			accent: {
    				DEFAULT: 'hsl(var(--accent))',
    				foreground: 'hsl(var(--accent-foreground))'
    			},
    			destructive: {
    				DEFAULT: 'hsl(var(--destructive))',
    				foreground: 'hsl(var(--destructive-foreground))'
    			},
    			border: 'hsl(var(--border))',
    			input: 'hsl(var(--input))',
    			ring: 'hsl(var(--ring))',
    			chart: {
    				'1': 'hsl(var(--chart-1))',
    				'2': 'hsl(var(--chart-2))',
    				'3': 'hsl(var(--chart-3))',
    				'4': 'hsl(var(--chart-4))',
    				'5': 'hsl(var(--chart-5))'
    			}
    		},
    		fontSize: {
    			'title-xxl': [
    				'44px',
    				'55px'
    			],
    			'title-xl': [
    				'36px',
    				'45px'
    			],
    			'title-xl2': [
    				'33px',
    				'45px'
    			],
    			'title-lg': [
    				'28px',
    				'35px'
    			],
    			'title-md': [
    				'24px',
    				'30px'
    			],
    			'title-md2': [
    				'26px',
    				'30px'
    			],
    			'title-sm': [
    				'20px',
    				'26px'
    			],
    			'title-xsm': [
    				'18px',
    				'24px'
    			]
    		},
    		spacing: {
    			'13': '52px',
    			'15': '60px',
    			'17': '68px',
    			'18': '72px',
    			'19': '76px',
    			'21': '84px',
    			'22': '88px',
    			'25': '100px',
    			'26': '104px',
    			'27': '108px',
    			'34': '136px',
    			'35': '140px',
    			'40': '160px',
    			'45': '180px',
    			'50': '200px',
    			'55': '220px',
    			'60': '240px',
    			'65': '260px',
    			'70': '280px',
    			'75': '300px',
    			'80': '320px',
    			'85': '340px',
    			'90': '360px',
    			'95': '380px',
    			'100': '400px',
    			'105': '420px',
    			'110': '440px',
    			'115': '460px',
    			'125': '500px',
    			'150': '600px',
    			'180': '720px',
    			'203': '812px',
    			'230': '920px',
    			'4.5': '18px',
    			'5.5': '22px',
    			'6.5': '26px',
    			'7.5': '30px',
    			'8.5': '34px',
    			'9.5': '38px',
    			'10.5': '42px',
    			'11.5': '46px',
    			'12.5': '50px',
    			'13.5': '54px',
    			'14.5': '58px',
    			'15.5': '62px',
    			'16.5': '66px',
    			'17.5': '70px',
    			'18.5': '74px',
    			'19.5': '78px',
    			'21.5': '86px',
    			'22.5': '90px',
    			'25.5': '102px',
    			'27.5': '110px',
    			'32.5': '130px',
    			'37.5': '150px',
    			'42.5': '170px',
    			'47.5': '190px',
    			'52.5': '210px',
    			'57.5': '230px',
    			'62.5': '250px',
    			'67.5': '270px',
    			'72.5': '290px',
    			'87.5': '350px',
    			'92.5': '370px',
    			'97.5': '390px',
    			'102.5': '410px',
    			'132.5': '530px',
    			'171.5': '686px',
    			'187.5': '750px',
    			'242.5': '970px'
    		},
    		maxWidth: {
    			'3': '12px',
    			'4': '16px',
    			'11': '44px',
    			'13': '52px',
    			'14': '56px',
    			'15': '60px',
    			'25': '100px',
    			'30': '120px',
    			'34': '136px',
    			'35': '140px',
    			'40': '160px',
    			'44': '176px',
    			'45': '180px',
    			'70': '280px',
    			'90': '360px',
    			'94': '376px',
    			'125': '500px',
    			'150': '600px',
    			'180': '720px',
    			'203': '812px',
    			'230': '920px',
    			'270': '1080px',
    			'280': '1120px',
    			'2.5': '10px',
    			'22.5': '90px',
    			'42.5': '170px',
    			'132.5': '530px',
    			'142.5': '570px',
    			'242.5': '970px',
    			'292.5': '1170px'
    		},
    		boxShadow: {
    			default: '0px 8px 13px -3px rgba(0, 0, 0, 0.07)',
    			card: '0px 1px 3px rgba(0, 0, 0, 0.12)',
    			'card-2': '0px 1px 2px rgba(0, 0, 0, 0.05)',
    			switcher: '0px 2px 4px rgba(0, 0, 0, 0.2)'
    		},
    		zIndex: {
    			'1': '1',
    			'9': '9',
    			'99': '99',
    			'999': '999',
    			'9999': '9999',
    			'99999': '99999',
    			'999999': '999999'
    		},
    		borderRadius: {
    			lg: 'var(--radius)',
    			md: 'calc(var(--radius) - 2px)',
    			sm: 'calc(var(--radius) - 4px)'
    		}
    	}
    },
	plugins: [require("tailwindcss-animate")],
};
