#pragma once
#ifndef ARITHMETIC_TRAITS_H
#define ARITHMETIC_TRAITS_H

/*	advc.enum: Arithmetic type traits. Enum types and ScaledNum types
	are treated as arithmetic. */
template<
	class T,
	bool bINTEGER = integer_limits<T>::is_integer,
	bool bENUM = enum_traits<T>::is_enum,
	bool bSCALED = is_scaled_num<T>::value>
struct arithm_traits
{
	static bool const is_arithmetic = false;
	static bool const is_signed = false;
};
template<class T>
struct arithm_traits<T, true, false, false>
{
	static bool const is_arithmetic = true;
	static T const min = integer_limits<T>::min;
	static T const max = integer_limits<T>::max;
	static bool const is_signed = integer_limits<T>::is_signed;
};
template<class T>
struct arithm_traits<T, false, true, false>
{
	static bool const is_arithmetic = true;
	/*	min and max are for asserting bounds. 'none' is often a sensible value,
		'len' usually isn't. */
	static int const min = std::min(enum_traits<T>::none, enum_traits<T>::first);
	static int const max = enum_traits<T>::len - 1;
	static bool const is_signed = true;
};
template<class T>
struct arithm_traits<T, false, false, true>
{
	static bool const is_arithmetic = true;
	static typename T::int_t const min = T::MIN;
	static typename T::int_t const max = T::MAX;
	static bool const is_signed = integer_limits<typename T::int_t>::is_signed;
};
template<>
struct arithm_traits<float>
{
	static bool const is_arithmetic = true;
	static float const min;
	static float const max;
	static bool const is_signed = true;
};
// (Can define only integral constants in-class)
float const arithm_traits<float>::min = FLT_MIN;
float const arithm_traits<float>::max = FLT_MAX;
template<>
struct arithm_traits<double>
{
	static bool const is_arithmetic = true;
	static double const min;
	static double const max;
	static bool const is_signed = true;
};
double const arithm_traits<double>::min = DBL_MIN;
double const arithm_traits<double>::max = DBL_MAX;

#endif
