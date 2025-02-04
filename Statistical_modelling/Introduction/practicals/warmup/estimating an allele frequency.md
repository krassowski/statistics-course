## The frequency of O blood group

In this section we will estimate the frequency of O blood group (as encoded by the [common
loss-of-function deletion in the ABO
gene](https://www.ensembl.org/Homo_sapiens/Variation/Explore?v=rs8176719), in multiple populations.

### An aside on the ABO blood group system.

The ABO blood group system was the first genetic polymorphism discovered in humans - [long before
the structure of DNA was solved](https://www.ncbi.nlm.nih.gov/books/NBK2267/). It was discovered by
studying agglutination patterns of red cells in serum from other individuals and is of course of
extreme relevance to blood transfusion. Beyond this, however, *ABO* is an interesting gene; the A/B
split seems to have been preserved [under balancing
selection](https://www.pnas.org/content/109/45/18493) across primates, while the O mutation itself
may be a recurrent polymorphism. ABO is also [one of the most pleiotropic loci in the human
genome](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5207801/) and there is evidence it is
[associated with risk of SARS-CoV-2
infection](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7594382/). 

But I was interested because it is also [protective against
malaria](https://www.nature.com/articles/s41467-019-13480-z). (The data here comes from that paper).

### Loading the data
First, let's load the data.

**Note.** I am using the [tidyverse](https://www.tidyverse.org) for these examples. If you don't
have it installed, either install it or use base R (e.g. `read.csv()`) instead.

```
library( tidyverse )
data = read_csv( "o_bld_grp.csv" )
```

**Question**.  What countries are in the data?  What ethnic groups?

The O blood group data is in the column called `O.bld.grp`. A `1` in this column means the
individual has O blood group (which happens if they have two copies of the above rs8176719
deletion). A `0` generally means they will have either A, AB, or B blood group depending on the
alleles they carry. (There are actually a few other mutations that cause loss of function of the *ABO* gene,
but we're ignoring them here.)

**Question**. Table this data for each population or ethnicity. Can you estimate the frequency in
each population? In each ethnic group?

### Building a model

You probably estimated the allele frequency as: the number of O individuals divided by the total
number of individuals.  If so congratulations - that's a sensible estimate!

But hang on... some of them vary quite a bit, don't they?

**Question.** How much do you trust these estimates? Do you trust them all as much as each other?  Why?

This course is all about handling uncertainty. We want to know **both** a good estimate, and how
uncertain that estimate is.  This is what statistical models are for!

Let's focus on a single population first - say Tanzania:

```
w = which( data$country == "Tanzania" )
> table( data$country[w], data$O.bld.grp[w] )
          
            0  1
  Tanzania 51 47
```

Counts like this can be modelled well using a [binomial distribution](../../notes/Distributions%20cheatsheet.pdf).  Let's do that now.

**Question**. If we use a binomial distribution to model these counts, what assumptions are we making?

The binomial distribution takes two parameters: `n`, the number of 'trials' (i.e. samples), and *&theta;*, the
frequency. (&theta; is called *p* on the [probability%20cheatsheet](../../notes/Probability%20cheatsheet.pdf), but we'll
call it &theta; here.)

The data is *k* - the number of O blood group alleles observed. Our conceptual model is that the population 'emits' O
blood group alleles at frequency &theta;. It is this frequency that we want to infer.

The basic inference formula (Bayes rule) is:

<img src="https://render.githubusercontent.com/render/math?math=P(\theta=x|\text{data}) = \frac{P(\text{data}|\theta=x) \cdot P(\theta=x)}{P(\text{data})}">

For the moment let us ignore the prior term *P(&theta;=x)*. Or to put it another way, we will assume it is uniform.

The term P(data|&theta;=x) is our *likelihood function*. This is what we will model with a binomial distribution. That
is, for the Tanzania data above we will assume:

<img src="https://render.githubusercontent.com/render/math?math=P\left(\text{data}|\theta=x\right) = \text{binom}\left( k=47 | n=98, \theta=x \right)">


**Note.** As in the [probability cheatsheet](../../notes/Probability%20cheatsheet.pdf) you must remember that all
probability is conditional. In all probabilities above we are assuming this *highly unrealistic* but *hopefully useful*
model in which a single frequency parameter governs O blood group in an entire human population. The probabilities
don't exist in the real world, but only in the model.

### Plotting the unnormalised posterior

**Question.** Given the counts for Tanzania above, plot the unnormalised posterior of the parameter &theta;. Also add
on a line showing your point estimate.

**Note.** Because we are using a flat prior and the normalising constant here, this is the same as plotting the
likelihood function - the only R function you really need for this is `dbinom()`. For readability it can be nice to
make a friendlier function matching the notation above:

```
binomial.likelihood <- function( k, n, theta ) {
    return( dbinom( x = k, size = n, prob = theta ) )
}
```

When you plot this you should see something like this:

<img src="solutions/Tanzania_o_blood_group_likelihood.svg">

**Note.** You did label your axes, right?  Hey, you must always label your axes!

**Question.** Can you make a grid of these plots, one per population?  One per ethnicity?

### Plotting the (fully normalised) posterior

In principle computing the posterior is not hard. We just need to compute the denominator of Bayes
theorem above, which (using the *law of total probability* from the [probability cheatsheet](../../notes/Probability%20cheatsheet.pdf)) is:

<img src="https://render.githubusercontent.com/render/math?math=P(\text{data}) = \int_y P(\text{data}|\theta=y) P(\theta=y)">

You could for example numerically compute this using the `integrate()` function - e.g. using the Tanzania counts above:

```
f <- function( y ) { return( binomial.likelihood( 47, 98, y ) ) ; }
denominator = integrate( f, 0, 1 )$value
```

It we now plot the (normalised) posterior, it looks the same as the likelihood but the y axis scale is different:

```
plot_normalised_posterior <- function( k, n ) {
	f <- function( y ) { return( binomial.likelihood( k, n, y ) ) ; }
	denominator = integrate( f, 0, 1 )$value

	x = seq( from = 0, to = 1, by = 0.01 )
	plot(
		x, binomial.likelihood( k = k, n = n, theta = x ) / denominator,
		type = 'l',
		xlab = "O blood group frequency (θ)",
		ylab = "Normalised posterior",
		yaxt = 'n',
		bty = 'n'
	)
	grid()
	abline( v = k/n, col = 'red' )
	axis( 2, las = 1 )
}
plot_normalised_posterior( 47, 98 )
```
<img src="solutions/Tanzania_o_blood_group_posterior.svg">

(If you stare at this a bit you'll see it looks about right in terms of the total mass under the function - which
should sum to 1).

### A Beta way to do it

In the general case solving the denominator can indeed be hard and require numerical integration like the above.
However, for this binomial model it turns out to be much easier. This is because the binomial has a 'conjugate' family of prior
distributions - the [Beta distribution](../../notes/Distributions%20cheatsheet.pdf).

If you stare at the Beta and binomial distributions [on the cheatsheet](../../notes/Distributions%20cheatsheet.pdf)
you'll see why this works. Using our notation here, the parameter &theta; (called *p* on the cheatsheet) enters the
binomial distribution pdf in the term:

<img src="https://render.githubusercontent.com/render/math?math=\theta^k (1-\theta)^n-k">

on the other hand, the frequency parameter of the Beta distribution (called *x*) on the cheatsheet) enters its pdf in the
similar term:

<img src="https://render.githubusercontent.com/render/math?math=\theta^{\alpha-1} (1-\theta)^{\beta-1}">

All the other terms are constant as far as the frequency parameter is concerned. What all this means is that **for a uniform (or
Beta) prior, and a binomial likelihood, the posterior distribution is a Beta distribution**:

<img src="https://render.githubusercontent.com/render/math?math=\text{Beta prior} \rightarrow \text{Binomial likelihood} \Rightarrow \text{Beta posterior}">

This relationship between prior and likelihood is known as 'conjugacy' - we say the Beta prior is conjugate to the Binomial
likelihood.

We can prove this for our data by adding it to our plot:

```
x = seq( from = 0, to = 1, by = 0.01 )
points( x, dbeta( x, shape1 = 47+1, shape2 = 51+1 ), type = 'l', lty = 2, col = 'blue' )
```

<img src="solutions/Tanzania_o_blood_group_posterior+beta.svg">

**Note.** The `+1s` are there in the above because of the way Beta is defined.  (It has exponents with `-1s`.)

### Comparing estimates

Having this analytical version of the posterior is good news. Here are two ways it helps. 

#### Easily summarising our inference about the parameter.

For example, we could summarise our inference by computing a **credible interval** for our parameter. A good interval
to take is a 95% posterior mass interavls, which you can form by chopping of 2.5% of the mass from both tails of the
distribution. If you want to see how to do this, look at the diagram [on the probability
cheatsheet](../../notes/Distributions%20cheatsheet.pdf). In R, the beta cdf is given by `pbeta()`, and its inverse (the
quantile function) by `qbeta()`. So we can do something like this:

```
compute.credible.interval <- function( k, n, mass = 0.95 ) {
	tail = 1-mass
	return( qbeta(
        c(
            lower = tail/2,
            median = 0.5,
            upper = 1.0-(tail/2)
        ),
        shape1 = k+1,
        shape2 = n-k+1
    ))
}
```

And let's use it to make a function to easily summarise any given subset of the data:
```
compute.counts <- function( data ) {
	return( c(
		nonO = length( which( data$O.bld.grp == 0 )),
		O = length( which( data$O.bld.grp == 1 ))
	))
}
summarise <- function( data.subset, name ) {
	counts = compute.counts( data.subset )
	credible = compute.credible.interval( counts[2], sum(counts ))
	return( c(
		list( name = name, nonO = counts[1], O = counts[2], estimate = counts[2]/sum(counts) ),
		credible
	))
}
```

**Question** Compute the 95% credible interval for all the populations. Compare to the sample size. (For example - can
you plot sample size vs size of credible interval?). What is the pattern?

**Question.** Do all the 95% credible intervals overlap? What about for individual ethnicities?

**Hint.** A neat way to do this is to use `map_dfr()` from the [purr package](https://github.com/rstudio/cheatsheets/blob/main/purrr.pdf):

```
countries = unique( data$country )
map_dfr( countries, function(country) { summarise( data[ data$country == country, ], country ) })

data$country_ethnicity = sprintf( "%s:%s", data$country, data$ethnicity )
ethnicities = unique( data$country_ethnicity )
map_dfr( ethnicities, function(ethnicity) { summarise( data[ data$country_ethnicity == ethnicity, ], ethnicity ) })
```

We could also add these to our plots - see the code in [`solutions/solutions.R`](solutions/solutions.R) for a working
version:

```
source( "solutions/solutions.R")
plot.bygroup( data, "country_ethnicity" )
```

<img src="solutions/all_ethnicities_o_blood_group_beta_posterior.svg">


#### Dealing with very uncertain estimates

Another way the conjugate prior / analytical formulation helps is in dealing with very uncertain estimates. For
example, the estimate for the `AKANS[ASHANTI_EASTERN]` has a point estimate of > 0.6 even though most of the others are
< 0.8. But this is based on only 21 observations. And what about the `Ghana:NORTHENER` or other groups where the
estimate is one or zero, but the counts are tiny?

One way we can deal with this is give up on the point estimate - just satisfy ourselves that there isn't much evidence.
For example, across all samples the joint estimate is `0.425`. How likely is it that the `AKANS[ASHANTI_EASTERN]`
estimate is larger than this?
```
> 1 - pbeta( 0.425, shape1 = 9, shape2 = 13 ) 
[1] 0.4301758
```

There's only 43% chance - that's a 57% chance the estimate is at or lower than the joint estimate.  

However, it can nevertheless be useful in lots of contexts to get a sensible point estimate, even when there is little
data. To do this let's replace our uniform prior with a *weakly informative prior*. This prior will say that we believe
O blood group is not at 0 or 100% frequency. If you followed the above, you'll see that we can just replace our uniform
prior with a `Beta(2,2)` prior.  Equivalently, we add 1 to boht the non-O and O counts in the data.  Try this:

```
plot.bygroup( data, "country_ethnicity", prior.counts = c(1,1) )
```

Now none of the estimates are 1 or zero, and all the credible intervals look at least somewhat sensible. Our prior has
**regularised** the estimation.

**Question**. Try adjusting the prior counts and seeing what happens to the estimates. Does it affect all populations
equally? How much prior data do you need to get all the estimates within 0.1 of each other?

**Note.** This technique is often used in practice. For example, the famous [EIGENSTRAT
software](https://www.nature.com/articles/ng1847) for computing principal components analysis estimates
allele frequencies in just this way - with a Beta(2,2) prior.
