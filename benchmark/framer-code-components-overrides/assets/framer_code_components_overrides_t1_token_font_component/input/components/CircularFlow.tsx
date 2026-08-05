import { useState, useEffect, useRef, useCallback, useMemo, startTransition } from "react"
import { addPropertyControls, ControlType, RenderTarget } from "framer"

// Constants
const ANIMATION_TIMINGS = {
	CIRCLE_END: 0.7,
	ARROW_START: 0.25,
	ARROW_DURATION: 0.3,
	TITLE_START: 0.05,
	TITLE_DURATION: 0.4,
	ANNOTATION_START: 0.7,
	ANNOTATION_DURATION: 0.3,
} as const

const STYLE_CONSTANTS = {
	TITLE_TRANSLATE_Y: 10,
	TITLE_MIN_OPACITY: 0.3,
	TITLE_OPACITY_RANGE: 0.7,
	ARROW_MIN_OPACITY: 0.3,
	ARROW_OPACITY_RANGE: 0.7,
	ARROW_TIP_MULTIPLIER: 0.7,
	ARROW_BASE_MULTIPLIER: 0.5,
	LABEL_TRANSLATE: 8,
	LABEL_MIN_OPACITY: 0.3,
	LABEL_OPACITY_RANGE: 0.7,
} as const

const STEP_POSITIONS = {
	top: { angle: -90, labelOffset: { x: 0, y: -1.4 } },
	right: { angle: 0, labelOffset: { x: 1.4, y: 0 } },
	bottom: { angle: 90, labelOffset: { x: 0, y: 1.4 } },
	left: { angle: 180, labelOffset: { x: -1.4, y: 0 } },
} as const

interface FontStyle {
	fontSize?: string | number
	variant?: string
	letterSpacing?: string
	lineHeight?: string
	fontFamily?: string
	fontWeight?: number
	fontStyle?: string
}

interface CircularFlowProps {
	centerTitle?: string
	stepTop?: string
	stepRight?: string
	stepBottom?: string
	stepLeft?: string
	accentColor?: string
	circleColor?: string
	textColor?: string
	labelTextColor?: string
	circleSize?: number
	strokeWidth?: number
	uppercase?: boolean
	annotation?: string
	annotationStep?: "top" | "right" | "bottom" | "left"
	scrollDriven?: boolean
	scrollStart?: number
	scrollEnd?: number
	titleFont?: FontStyle
	labelFont?: FontStyle
}

/**
 * Circular Flow Diagram
 *
 * @framerSupportedLayoutWidth fixed
 * @framerSupportedLayoutHeight fixed
 */
export default function CircularFlow(props: CircularFlowProps) {
	const {
		centerTitle = "Process\nFlow",
		stepTop = "Plan",
		stepRight = "Execute",
		stepBottom = "Review",
		stepLeft = "Improve",
		accentColor = "#0099FF",
		circleColor = "#000000",
		textColor = "#000000",
		labelTextColor = "#666666",
		circleSize = 200,
		strokeWidth = 2,
		uppercase = false,
		annotation = "",
		annotationStep = "top",
		scrollDriven = false,
		scrollStart = 0,
		scrollEnd = 100,
		titleFont = {
			fontSize: "24px",
			variant: "Bold",
			letterSpacing: "-0.02em",
		},
		labelFont = {
			fontSize: "14px",
			variant: "Medium",
			letterSpacing: "-0.01em",
		},
	} = props

	const containerRef = useRef<HTMLDivElement | null>(null)
	const rafRef = useRef<number>(0)
	const [progress, setProgress] = useState(scrollDriven ? 0 : 1)
	const [dimensions, setDimensions] = useState({ width: 400, height: 400 })

	const formatText = useCallback((text: string) => (uppercase ? text.toUpperCase() : text), [uppercase])

	const titleLines = useMemo(() => centerTitle.split("\n"), [centerTitle])

	const radius = useMemo(() => circleSize / 2, [circleSize])
	const circumference = useMemo(() => 2 * Math.PI * radius, [radius])

	const centerX = useMemo(() => dimensions.width / 2, [dimensions.width])
	const centerY = useMemo(() => dimensions.height / 2, [dimensions.height])

	const arrowSize = useMemo(() => strokeWidth * 4, [strokeWidth])

	// Animation progress calculations
	const circleProgress = useMemo(
		() => Math.min(progress / ANIMATION_TIMINGS.CIRCLE_END, 1),
		[progress]
	)
	const dashOffset = useMemo(
		() => circumference * (1 - circleProgress),
		[circumference, circleProgress]
	)

	const arrowProgress = useMemo(() => {
		return progress < ANIMATION_TIMINGS.ARROW_START
			? 0
			: Math.min(
					(progress - ANIMATION_TIMINGS.ARROW_START) / ANIMATION_TIMINGS.ARROW_DURATION,
					1
			  )
	}, [progress])

	const arrowOpacity = useMemo(
		() => STYLE_CONSTANTS.ARROW_MIN_OPACITY + arrowProgress * STYLE_CONSTANTS.ARROW_OPACITY_RANGE,
		[arrowProgress]
	)

	const titleProgress = useMemo(() => {
		return progress < ANIMATION_TIMINGS.TITLE_START
			? 0
			: Math.min(
					(progress - ANIMATION_TIMINGS.TITLE_START) / ANIMATION_TIMINGS.TITLE_DURATION,
					1
			  )
	}, [progress])

	const annotationProgress = useMemo(() => {
		return progress < ANIMATION_TIMINGS.ANNOTATION_START
			? 0
			: Math.min(
					(progress - ANIMATION_TIMINGS.ANNOTATION_START) /
						ANIMATION_TIMINGS.ANNOTATION_DURATION,
					1
			  )
	}, [progress])

	const buildTitleElements = useCallback(() => {
		return titleLines.map((line, idx) => {
			const text = uppercase ? line.toUpperCase() : line
			const style = {
				fontFamily: titleFont?.fontFamily,
				fontSize: titleFont?.fontSize,
				fontWeight: titleFont?.fontWeight,
				fontStyle: titleFont?.fontStyle,
				letterSpacing: titleFont?.letterSpacing,
				color: textColor,
				lineHeight: "1.1",
				whiteSpace: "nowrap" as const,
				transform: `translateY(${(1 - titleProgress) * STYLE_CONSTANTS.TITLE_TRANSLATE_Y}px)`,
				opacity:
					STYLE_CONSTANTS.TITLE_MIN_OPACITY + titleProgress * STYLE_CONSTANTS.TITLE_OPACITY_RANGE,
			}
			return (
				<div key={idx} style={style}>
					{text}
				</div>
			)
		})
	}, [titleLines, titleFont, textColor, titleProgress, uppercase])

	const buildArrowElements = useCallback(() => {
		const angles = [-45, 45, 135, 225]

		return angles.map((angleDeg, idx) => {
			const angleRad = (angleDeg * Math.PI) / 180
			const pointX = centerX + radius * Math.cos(angleRad)
			const pointY = centerY + radius * Math.sin(angleRad)
			const tangentAngle = angleRad + Math.PI / 2
			const tipX = pointX + arrowSize * STYLE_CONSTANTS.ARROW_TIP_MULTIPLIER * Math.cos(tangentAngle)
			const tipY = pointY + arrowSize * STYLE_CONSTANTS.ARROW_TIP_MULTIPLIER * Math.sin(tangentAngle)
			const base1X = pointX + arrowSize * STYLE_CONSTANTS.ARROW_BASE_MULTIPLIER * Math.cos(angleRad)
			const base1Y = pointY + arrowSize * STYLE_CONSTANTS.ARROW_BASE_MULTIPLIER * Math.sin(angleRad)
			const base2X = pointX - arrowSize * STYLE_CONSTANTS.ARROW_BASE_MULTIPLIER * Math.cos(angleRad)
			const base2Y = pointY - arrowSize * STYLE_CONSTANTS.ARROW_BASE_MULTIPLIER * Math.sin(angleRad)
			const points = `${base1X},${base1Y} ${tipX},${tipY} ${base2X},${base2Y}`

			return (
				<polygon
					key={idx}
					points={points}
					fill={circleColor}
					opacity={arrowOpacity}
					aria-label={`Arrow ${idx + 1}`}
				/>
			)
		})
	}, [centerX, centerY, radius, arrowSize, circleColor, arrowOpacity])

	const titleElements = useMemo(() => buildTitleElements(), [buildTitleElements])
	const arrowElements = useMemo(() => buildArrowElements(), [buildArrowElements])

	const updateDimensions = useCallback(() => {
		if (!containerRef.current) return
		const { width, height } = containerRef.current.getBoundingClientRect()
		setDimensions({ width, height })
	}, [])

	useEffect(() => {
		if (typeof window === "undefined") return
		updateDimensions()

		const resizeObserver = new ResizeObserver(() => {
			if (rafRef.current) cancelAnimationFrame(rafRef.current)
			rafRef.current = requestAnimationFrame(updateDimensions)
		})

		if (containerRef.current) {
			resizeObserver.observe(containerRef.current)
		}

		return () => {
			if (rafRef.current) cancelAnimationFrame(rafRef.current)
			resizeObserver.disconnect()
		}
	}, [updateDimensions])

	useEffect(() => {
		if (!scrollDriven || typeof window === "undefined") {
			startTransition(() => setProgress(1))
			return
		}

		const handleScroll = () => {
			const scrollY = window.scrollY
			const windowHeight = window.innerHeight
			const docHeight = document.documentElement.scrollHeight

			const scrollRange = docHeight - windowHeight
			const scrollPercent = scrollRange > 0 ? (scrollY / scrollRange) * 100 : 0

			let newProgress = 0
			if (scrollPercent <= scrollStart) {
				newProgress = 0
			} else if (scrollPercent >= scrollEnd) {
				newProgress = 1
			} else {
				newProgress = (scrollPercent - scrollStart) / (scrollEnd - scrollStart)
			}

			startTransition(() => setProgress(newProgress))
		}

		handleScroll()
		window.addEventListener("scroll", handleScroll, { passive: true })
		return () => window.removeEventListener("scroll", handleScroll)
	}, [scrollDriven, scrollStart, scrollEnd])

	const renderStepLabel = useCallback(
		(step: "top" | "right" | "bottom" | "left", text: string) => {
			const { angle, labelOffset } = STEP_POSITIONS[step]
			const angleRad = (angle * Math.PI) / 180
			const labelX = centerX + radius * Math.cos(angleRad)
			const labelY = centerY + radius * Math.sin(angleRad)
			const offsetX = labelOffset.x * radius
			const offsetY = labelOffset.y * radius

			const labelProgress =
				progress < ANIMATION_TIMINGS.ARROW_START + 0.1
					? 0
					: Math.min((progress - (ANIMATION_TIMINGS.ARROW_START + 0.1)) / 0.3, 1)

			const translateAmount = (1 - labelProgress) * STYLE_CONSTANTS.LABEL_TRANSLATE
			const opacity =
				STYLE_CONSTANTS.LABEL_MIN_OPACITY + labelProgress * STYLE_CONSTANTS.LABEL_OPACITY_RANGE

			const isAnnotated = annotation && annotationStep === step

			return (
				<div
					key={step}
					style={{
						position: "absolute",
						left: `${labelX + offsetX}px`,
						top: `${labelY + offsetY}px`,
						transform: `translate(-50%, -50%) translateY(${translateAmount}px)`,
						opacity,
						fontFamily: labelFont?.fontFamily,
						fontSize: labelFont?.fontSize,
						letterSpacing: labelFont?.letterSpacing,
						fontStyle: labelFont?.fontStyle,
						color: isAnnotated ? accentColor : labelTextColor,
						fontWeight: isAnnotated ? 600 : labelFont?.fontWeight,
						whiteSpace: "nowrap",
						textAlign: "center",
					}}
				>
					{formatText(text)}
					{isAnnotated && annotation && (
						<div
							style={{
								marginTop: "4px",
								fontSize: "12px",
								opacity: annotationProgress,
								transform: `translateY(${(1 - annotationProgress) * 5}px)`,
							}}
						>
							{formatText(annotation)}
						</div>
					)}
				</div>
			)
		},
		[
			centerX,
			centerY,
			radius,
			progress,
			labelFont,
			labelTextColor,
			accentColor,
			annotation,
			annotationStep,
			annotationProgress,
			formatText,
		]
	)

	return (
		<div
			ref={containerRef}
			style={{
				width: "100%",
				height: "100%",
				position: "relative",
				display: "flex",
				alignItems: "center",
				justifyContent: "center",
			}}
			role="img"
			aria-label="Circular flow diagram showing a continuous process"
		>
			<svg
				width={dimensions.width}
				height={dimensions.height}
				style={{ position: "absolute", top: 0, left: 0 }}
				aria-hidden="true"
			>
				<circle
					cx={centerX}
					cy={centerY}
					r={radius}
					fill="none"
					stroke={circleColor}
					strokeWidth={strokeWidth}
					strokeDasharray={circumference}
					strokeDashoffset={dashOffset}
					style={{ transition: scrollDriven ? "none" : "stroke-dashoffset 0.3s ease-out" }}
				/>
				{arrowElements}
			</svg>

			<div
				style={{
					position: "absolute",
					display: "flex",
					flexDirection: "column",
					alignItems: "center",
					justifyContent: "center",
					textAlign: "center",
					gap: "4px",
				}}
			>
				{titleElements}
			</div>

			{renderStepLabel("top", stepTop)}
			{renderStepLabel("right", stepRight)}
			{renderStepLabel("bottom", stepBottom)}
			{renderStepLabel("left", stepLeft)}
		</div>
	)
}

CircularFlow.displayName = "CircularFlow"

addPropertyControls(CircularFlow, {
	centerTitle: {
		type: ControlType.String,
		title: "Center Title",
		defaultValue: "Process\nFlow",
		displayTextArea: true,
	},
	stepTop: {
		type: ControlType.String,
		title: "Top Step",
		defaultValue: "Plan",
	},
	stepRight: {
		type: ControlType.String,
		title: "Right Step",
		defaultValue: "Execute",
	},
	stepBottom: {
		type: ControlType.String,
		title: "Bottom Step",
		defaultValue: "Review",
	},
	stepLeft: {
		type: ControlType.String,
		title: "Left Step",
		defaultValue: "Improve",
	},
	accentColor: {
		type: ControlType.Color,
		title: "Accent Color",
		defaultValue: "#0099FF",
	},
	circleColor: {
		type: ControlType.Color,
		title: "Circle Color",
		defaultValue: "#000000",
	},
	textColor: {
		type: ControlType.Color,
		title: "Text Color",
		defaultValue: "#000000",
	},
	labelTextColor: {
		type: ControlType.Color,
		title: "Label Color",
		defaultValue: "#666666",
	},
	circleSize: {
		type: ControlType.Number,
		title: "Circle Size",
		defaultValue: 200,
		min: 100,
		max: 400,
		step: 10,
	},
	strokeWidth: {
		type: ControlType.Number,
		title: "Stroke Width",
		defaultValue: 2,
		min: 1,
		max: 10,
		step: 1,
	},
	uppercase: {
		type: ControlType.Boolean,
		title: "Uppercase",
		defaultValue: false,
		enabledTitle: "Yes",
		disabledTitle: "No",
	},
	annotation: {
		type: ControlType.String,
		title: "Annotation",
		defaultValue: "",
	},
	annotationStep: {
		type: ControlType.Enum,
		title: "Annotate Step",
		options: ["top", "right", "bottom", "left"],
		optionTitles: ["Top", "Right", "Bottom", "Left"],
		defaultValue: "top",
		hidden: ({ annotation }) => !annotation,
	},
	scrollDriven: {
		type: ControlType.Boolean,
		title: "Scroll Driven",
		defaultValue: false,
		enabledTitle: "Yes",
		disabledTitle: "No",
	},
	scrollStart: {
		type: ControlType.Number,
		title: "Scroll Start",
		defaultValue: 0,
		min: 0,
		max: 100,
		step: 1,
		unit: "%",
		hidden: ({ scrollDriven }) => !scrollDriven,
	},
	scrollEnd: {
		type: ControlType.Number,
		title: "Scroll End",
		defaultValue: 100,
		min: 0,
		max: 100,
		step: 1,
		unit: "%",
		hidden: ({ scrollDriven }) => !scrollDriven,
	},
	titleFont: {
		type: ControlType.Font,
		title: "Title Font",
		controls: "extended",
		defaultFontType: "sans-serif",
		defaultValue: {
			fontSize: "24px",
			variant: "Bold",
			letterSpacing: "-0.02em",
		},
	},
	labelFont: {
		type: ControlType.Font,
		title: "Label Font",
		controls: "extended",
		defaultFontType: "sans-serif",
		defaultValue: {
			fontSize: "14px",
			variant: "Medium",
			letterSpacing: "-0.01em",
		},
	},
})