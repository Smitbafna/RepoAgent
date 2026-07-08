import { Input as InputPrimitive } from "@base-ui/react/input"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const inputVariants = cva(
  "flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "",
        destructive: "border-destructive focus-visible:ring-destructive",
      },
      inputSize: {
        default: "h-10",
        sm: "h-9",
        lg: "h-12",
      },
    },
    defaultVariants: {
      variant: "default",
      inputSize: "default",
    },
  }
)

function Input({
  className,
  variant,
  inputSize,
  type,
  ...props
}: InputPrimitive.Props & VariantProps<typeof inputVariants> & { type?: string }) {
  return (
    <InputPrimitive
      data-slot="input"
      type={type}
      className={cn(inputVariants({ variant, inputSize, className }))}
      {...props}
    />
  )
}

export { Input }